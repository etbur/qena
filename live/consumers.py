"""
Real-time WebSocket consumer — Qenagebeya Live Streams
Django Channels 4.x + InMemoryChannelLayer

FLOW
────
1. Vendor  → camera starts → sends {webrtc_offer_broadcast}
2. Server  → stores host_channel, broadcasts {host_camera_ready} to all viewers
3. Viewer  → sends {request_offer}
4. Server  → forwards as {viewer_joined} to host
5. Host    → creates RTCPeerConnection per viewer, sends {webrtc_offer, sdp, target_channel}
6. Viewer  → answers {webrtc_answer, sdp}  (routed to host via DB host_channel lookup)
7. Both    → {ice_candidate, candidate, target_channel}  (direct point-to-point)

Viewer mic/cam:
 Viewer requests  → vendor grants (mic_granted + host_channel sent to viewer)
 Viewer opens mic → {mic_offer, sdp} → host
 Host answers     → {mic_answer, sdp, target_channel} → viewer
 ICE              → both directions with target_channel
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.db.models import F

log = logging.getLogger('live')

ALLOWED_REACTIONS = {'❤️', '🔥', '👏', '😍', '🎉', '😂', '🙌', '💯'}


class LiveConsumer(AsyncWebsocketConsumer):

    # ── lifecycle ────────────────────────────────────────────────────────────

    async def connect(self):
        self.stream_uuid = self.scope['url_route']['kwargs']['stream_uuid']
        self.group_name  = f'live_{self.stream_uuid.replace("-", "")}'
        self.user        = self.scope.get('user')
        self.stream_id   = None
        self.is_host     = False

        # Display name
        if self.user and getattr(self.user, 'is_authenticated', False):
            name = (self.user.get_full_name() or self.user.username).strip()
            self.username = name or f'User{self.user.pk}'
        else:
            self.username = f'Guest{abs(hash(self.channel_name)) % 9999}'

        stream = await _db_get_stream(self.stream_uuid)
        if not stream:
            await self.close(code=4004)
            return

        self.stream_id = stream['pk']
        if self.user and getattr(self.user, 'is_authenticated', False):
            self.is_host = (stream['vendor_user_id'] == self.user.pk)

        # Join group + accept
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Increment live viewer counter
        await _db_increment_live(self.stream_id)

        # Send initial stream state to this client (paused status, stream details)
        await self.send(text_data=json.dumps({
            'type': 'stream_status',
            'status': stream.get('status', 'live'),
            'is_paused': stream.get('is_paused', False),
            'has_host': bool(stream.get('host_channel')),
        }))

        # If host camera is already active, notify viewer immediately
        if not self.is_host and stream.get('host_channel'):
            await self.send(text_data=json.dumps({
                'type': 'host_camera_ready',
                'host_channel': stream['host_channel'],
            }))

        # Send chat history to this client only
        history = await _db_get_history(self.stream_id)
        await self.send(text_data=json.dumps({'type': 'history', 'messages': history}))

        # Announce join
        await self.channel_layer.group_send(self.group_name, {
            'type': 'ws.chat', 'msg_type': 'system',
            'username': 'System', 'text': f'👋 {self.username} joined',
            'avatar': '🌐', 'is_host': False,
        })

        # Tell vendor dashboard about this viewer
        await self.channel_layer.group_send(self.group_name, {
            'type': 'ws.viewer_announce',
            'channel': self.channel_name,
            'username': self.username,
        })

        # Push updated live viewer count
        count = await _db_get_live(self.stream_id)
        await self.channel_layer.group_send(self.group_name, {
            'type': 'ws.viewers', 'count': count,
        })

    async def disconnect(self, close_code):
        if not hasattr(self, 'group_name'):
            return
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        if not self.stream_id:
            return

        # Decrement live viewer counter
        await _db_decrement_live(self.stream_id)

        # Clear host channel when vendor disconnects
        if self.is_host:
            await _db_clear_host_channel(self.stream_id, self.channel_name)

        await self.channel_layer.group_send(self.group_name, {
            'type': 'ws.chat', 'msg_type': 'system',
            'username': 'System', 'text': f'👋 {self.username} left',
            'avatar': '🌐', 'is_host': False,
        })

        count = await _db_get_live(self.stream_id)
        await self.channel_layer.group_send(self.group_name, {
            'type': 'ws.viewers', 'count': max(0, count),
        })

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, TypeError):
            return

        t = data.get('type', '')

        # ── Chat ────────────────────────────────────────────────────────────
        if t == 'chat':
            text = str(data.get('text', '')).strip()[:300]
            if not text:
                return
            user_obj = self.user if getattr(self.user, 'is_authenticated', False) else None
            await _db_save_msg(self.stream_id, 'chat', self.username, text, user_obj)
            await self.channel_layer.group_send(self.group_name, {
                'type': 'ws.chat', 'msg_type': 'chat',
                'username': self.username, 'text': text,
                'avatar': self.username[0].upper(), 'is_host': self.is_host,
            })

        elif t == 'question':
            text = str(data.get('text', '')).strip()[:300]
            if not text:
                return
            user_obj = self.user if getattr(self.user, 'is_authenticated', False) else None
            await _db_save_msg(self.stream_id, 'question', self.username, f'❓ {text}', user_obj)
            await self.channel_layer.group_send(self.group_name, {
                'type': 'ws.chat', 'msg_type': 'question',
                'username': self.username, 'text': f'❓ {text}',
                'avatar': self.username[0].upper(), 'is_host': False,
            })

        # ── Reaction ────────────────────────────────────────────────────────
        elif t == 'reaction':
            emoji = data.get('emoji', '❤️')
            if emoji not in ALLOWED_REACTIONS:
                emoji = '❤️'
            await _db_increment_likes(self.stream_id)
            await self.channel_layer.group_send(self.group_name, {
                'type': 'ws.reaction', 'emoji': emoji, 'username': self.username,
            })

        # ── Pin product (host only) ──────────────────────────────────────────
        elif t == 'pin_product' and self.is_host:
            try:
                pid = int(data.get('product_id', 0))
            except (ValueError, TypeError):
                return
            product = await _db_pin_product(self.stream_id, pid)
            if product:
                await self.channel_layer.group_send(self.group_name, {
                    'type': 'ws.pin',
                    'product_name': product['name'], 'product_price': product['price'],
                    'product_img': product['image'], 'product_url': product['url'],
                })

        # ── Pause / Resume stream (host only) ────────────────────────────────
        elif t == 'pause_stream' and self.is_host:
            await _db_set_pause_status(self.stream_id, True)
            await self.channel_layer.group_send(self.group_name, {
                'type': 'ws.stream_pause', 'is_paused': True,
            })
            await self.channel_layer.group_send(self.group_name, {
                'type': 'ws.chat', 'msg_type': 'system', 'username': 'System',
                'text': '⏸️ Stream paused by host', 'avatar': '⏸️', 'is_host': True,
            })

        elif t == 'resume_stream' and self.is_host:
            await _db_set_pause_status(self.stream_id, False)
            await self.channel_layer.group_send(self.group_name, {
                'type': 'ws.stream_pause', 'is_paused': False,
            })
            await self.channel_layer.group_send(self.group_name, {
                'type': 'ws.chat', 'msg_type': 'system', 'username': 'System',
                'text': '▶️ Stream resumed by host', 'avatar': '▶️', 'is_host': True,
            })

        # ── End stream (host only) ───────────────────────────────────────────
        elif t == 'end_stream' and self.is_host:
            await _db_end_stream(self.stream_id)
            await self.channel_layer.group_send(self.group_name, {'type': 'ws.end'})

        # ══ WebRTC — main stream (host → viewers) ════════════════════════════

        # Host camera ready → notify all viewers
        elif t == 'webrtc_offer_broadcast' and self.is_host:
            await _db_set_host_channel(self.stream_id, self.channel_name)
            await self.channel_layer.group_send(self.group_name, {
                'type': 'ws.host_ready', 'host_channel': self.channel_name,
            })

        # Host stops camera
        elif t == 'stop_camera' and self.is_host:
            await _db_clear_host_channel(self.stream_id, self.channel_name)
            await self.channel_layer.group_send(self.group_name, {
                'type': 'ws.host_stopped_camera',
            })

        # Host sends SDP offer to one viewer
        elif t == 'webrtc_offer' and self.is_host:
            target = data.get('target_channel')
            if target:
                await self.channel_layer.send(target, {
                    'type': 'ws.webrtc_offer',
                    'sdp': data.get('sdp', ''),
                    'from_channel': self.channel_name,
                })

        # Viewer sends SDP answer to host
        elif t == 'webrtc_answer' and not self.is_host:
            host_ch = await _db_get_host_channel(self.stream_id)
            if host_ch:
                await self.channel_layer.send(host_ch, {
                    'type': 'ws.webrtc_answer',
                    'sdp': data.get('sdp', ''),
                    'from_channel': self.channel_name,
                })

        # ICE candidate (point-to-point via target_channel)
        elif t == 'ice_candidate':
            target    = data.get('target_channel')
            candidate = data.get('candidate', '')
            if target and target != self.channel_name:
                await self.channel_layer.send(target, {
                    'type': 'ws.ice_candidate',
                    'candidate': candidate,
                    'from_channel': self.channel_name,
                })

        # Viewer requests offer (late joiner or reconnect)
        elif t == 'request_offer' and not self.is_host:
            host_ch = await _db_get_host_channel(self.stream_id)
            if host_ch:
                await self.channel_layer.send(host_ch, {
                    'type': 'ws.viewer_joined',
                    'from_channel': self.channel_name,
                })

        # ══ Viewer presence ════════════════════════════════════════════════

        elif t == 'viewer_announce':
            await self.channel_layer.group_send(self.group_name, {
                'type': 'ws.viewer_announce',
                'channel': self.channel_name, 'username': self.username,
            })

        elif t == 'raise_hand' and not self.is_host:
            req_type = data.get('req_type', 'mic')
            await self.channel_layer.group_send(self.group_name, {
                'type': 'ws.raise_hand',
                'channel': self.channel_name,
                'username': self.username,
                'req_type': req_type,
            })

        elif t == 'lower_hand' and not self.is_host:
            await self.channel_layer.group_send(self.group_name, {
                'type': 'ws.lower_hand',
                'channel': self.channel_name, 'username': self.username,
            })

        # ══ Viewer mic/cam grant ════════════════════════════════════════════

        elif t == 'grant_mic' and self.is_host:
            target   = data.get('target_channel')
            req_type = data.get('req_type', 'mic')
            if target:
                # FIX: send host_channel to viewer so ICE candidates are routed correctly
                await self.channel_layer.send(target, {
                    'type': 'ws.mic_granted',
                    'req_type': req_type,
                    'host_channel': self.channel_name,
                })
                label = {'mic': '🎤 mic', 'camera': '📷 camera', 'both': '🎤📷 mic+cam'}.get(req_type, '🎤 mic')
                await self.channel_layer.group_send(self.group_name, {
                    'type': 'ws.chat', 'msg_type': 'system', 'username': 'System',
                    'text': f'{label} granted to {data.get("username", "Viewer")}',
                    'avatar': '🎤', 'is_host': False,
                })

        elif t == 'revoke_mic' and self.is_host:
            target = data.get('target_channel')
            if target:
                await self.channel_layer.send(target, {'type': 'ws.mic_revoked'})

        # Viewer sends mic/cam SDP offer to host
        elif t == 'mic_offer' and not self.is_host:
            host_ch = await _db_get_host_channel(self.stream_id)
            if host_ch:
                await self.channel_layer.send(host_ch, {
                    'type': 'ws.mic_offer',
                    'sdp': data.get('sdp', ''),
                    'from_channel': self.channel_name,
                    'username': self.username,
                })

        # Host sends mic answer to viewer
        elif t == 'mic_answer' and self.is_host:
            target = data.get('target_channel')
            if target:
                await self.channel_layer.send(target, {
                    'type': 'ws.mic_answer',
                    'sdp': data.get('sdp', ''),
                })

    # ── Group event handlers ──────────────────────────────────────────────────

    async def ws_chat(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat', 'msg_type': event.get('msg_type', 'chat'),
            'username': event['username'], 'text': event['text'],
            'avatar': event.get('avatar', '?'), 'is_host': event.get('is_host', False),
        }))

    async def ws_viewers(self, event):
        await self.send(text_data=json.dumps({'type': 'viewer_count', 'count': event['count']}))

    async def ws_reaction(self, event):
        await self.send(text_data=json.dumps({
            'type': 'reaction', 'emoji': event['emoji'], 'username': event['username'],
        }))

    async def ws_pin(self, event):
        await self.send(text_data=json.dumps({
            'type': 'product_pin',
            'product_name': event['product_name'], 'product_price': event['product_price'],
            'product_img': event['product_img'], 'product_url': event['product_url'],
        }))

    async def ws_end(self, event):
        await self.send(text_data=json.dumps({'type': 'stream_ended'}))

    async def ws_stream_pause(self, event):
        await self.send(text_data=json.dumps({
            'type': 'stream_pause_status',
            'is_paused': event.get('is_paused', False),
        }))

    async def ws_webrtc_offer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'webrtc_offer', 'sdp': event['sdp'],
            'from_channel': event['from_channel'],
        }))

    async def ws_webrtc_answer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'webrtc_answer', 'sdp': event['sdp'],
            'from_channel': event['from_channel'],
        }))

    async def ws_ice_candidate(self, event):
        await self.send(text_data=json.dumps({
            'type': 'ice_candidate', 'candidate': event['candidate'],
            'from_channel': event['from_channel'],
        }))

    async def ws_viewer_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'viewer_joined', 'from_channel': event['from_channel'],
        }))

    async def ws_host_ready(self, event):
        if not self.is_host:
            await self.send(text_data=json.dumps({
                'type': 'host_camera_ready', 'host_channel': event['host_channel'],
            }))

    async def ws_host_stopped_camera(self, event):
        if not self.is_host:
            await self.send(text_data=json.dumps({
                'type': 'host_stopped_camera',
            }))

    async def ws_viewer_announce(self, event):
        await self.send(text_data=json.dumps({
            'type': 'viewer_announce',
            'channel': event['channel'], 'username': event['username'],
        }))

    async def ws_raise_hand(self, event):
        await self.send(text_data=json.dumps({
            'type': 'raise_hand', 'channel': event['channel'],
            'username': event['username'], 'req_type': event.get('req_type', 'mic'),
        }))

    async def ws_lower_hand(self, event):
        await self.send(text_data=json.dumps({
            'type': 'lower_hand', 'channel': event['channel'], 'username': event['username'],
        }))

    async def ws_mic_granted(self, event):
        # FIX: deliver host_channel so viewer can target ICE candidates correctly
        await self.send(text_data=json.dumps({
            'type': 'mic_granted',
            'req_type': event.get('req_type', 'mic'),
            'host_channel': event.get('host_channel', ''),
        }))

    async def ws_mic_revoked(self, event):
        await self.send(text_data=json.dumps({'type': 'mic_revoked'}))

    async def ws_mic_offer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'mic_offer', 'sdp': event['sdp'],
            'from_channel': event['from_channel'], 'username': event['username'],
        }))

    async def ws_mic_answer(self, event):
        await self.send(text_data=json.dumps({'type': 'mic_answer', 'sdp': event['sdp']}))


# ── DB helpers ────────────────────────────────────────────────────────────────

@database_sync_to_async
def _db_get_stream(uuid_str):
    from live.models import LiveStream
    try:
        s = LiveStream.objects.select_related('vendor').get(stream_id=uuid_str)
        return {
            'pk': s.pk,
            'status': s.status,
            'vendor_user_id': s.vendor.user_id,
            'is_paused': s.is_paused,
            'host_channel': s.host_channel,
        }
    except LiveStream.DoesNotExist:
        return None


@database_sync_to_async
def _db_set_pause_status(stream_pk, is_paused):
    from live.models import LiveStream
    LiveStream.objects.filter(pk=stream_pk).update(is_paused=is_paused)


@database_sync_to_async
def _db_increment_live(pk):
    from live.models import LiveStream
    LiveStream.objects.filter(pk=pk).update(
        total_views=F('total_views') + 1,
        live_viewers=F('live_viewers') + 1,
    )


@database_sync_to_async
def _db_decrement_live(pk):
    from live.models import LiveStream
    LiveStream.objects.filter(pk=pk, live_viewers__gt=0).update(
        live_viewers=F('live_viewers') - 1,
    )


@database_sync_to_async
def _db_get_live(pk):
    from live.models import LiveStream
    try:
        return LiveStream.objects.values_list('live_viewers', flat=True).get(pk=pk)
    except Exception:
        return 0


@database_sync_to_async
def _db_increment_likes(pk):
    from live.models import LiveStream
    LiveStream.objects.filter(pk=pk).update(total_likes=F('total_likes') + 1)


@database_sync_to_async
def _db_save_msg(stream_pk, msg_type, username, text, user_obj):
    from live.models import LiveChat, LiveStream
    LiveChat.objects.create(
        stream_id=stream_pk, user=user_obj,
        username=username, msg_type=msg_type, text=text,
    )
    LiveStream.objects.filter(pk=stream_pk).update(total_messages=F('total_messages') + 1)


@database_sync_to_async
def _db_get_history(stream_pk, limit=60):
    from live.models import LiveChat
    msgs = list(
        LiveChat.objects
        .filter(stream_id=stream_pk)
        .order_by('created_at')
        .values('msg_type', 'username', 'text')[:limit]
    )
    return [
        {
            'msg_type': m['msg_type'],
            'username': m['username'] or 'Guest',
            'text':     m['text'],
            'avatar':   (m['username'] or 'G')[0].upper(),
            'is_host':  False,
        }
        for m in msgs
    ]


@database_sync_to_async
def _db_pin_product(stream_pk, product_id):
    from live.models import LiveStream
    from store.models import Product
    try:
        p = Product.objects.get(pk=product_id, is_active=True)
        LiveStream.objects.filter(pk=stream_pk).update(pinned_product=p)
        return {
            'name': p.name, 'price': str(p.price),
            'image': p.image.url if p.image else '',
            'url': p.get_absolute_url(),
        }
    except Exception:
        return None


@database_sync_to_async
def _db_end_stream(stream_pk):
    from live.models import LiveStream
    LiveStream.objects.filter(pk=stream_pk).update(
        status=LiveStream.STATUS_ENDED,
        ended_at=timezone.now(),
        host_channel='',
        live_viewers=0,
    )


@database_sync_to_async
def _db_set_host_channel(stream_pk, channel_name):
    from live.models import LiveStream
    LiveStream.objects.filter(pk=stream_pk).update(host_channel=channel_name)


@database_sync_to_async
def _db_clear_host_channel(stream_pk, channel_name):
    """Only clear if it's still this channel (avoid clearing a new session's channel)."""
    from live.models import LiveStream
    LiveStream.objects.filter(pk=stream_pk, host_channel=channel_name).update(host_channel='')


@database_sync_to_async
def _db_get_host_channel(stream_pk):
    from live.models import LiveStream
    try:
        return LiveStream.objects.values_list('host_channel', flat=True).get(pk=stream_pk)
    except Exception:
        return None

"""
WebSocket consumer test using channels.testing.
Run: python test_ws.py
"""
import os, sys, asyncio, json
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
import django; django.setup()

from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from qenagebeya.asgi import application


async def recv(comm, timeout=4):
    """Receive one JSON message, return None on timeout/disconnect."""
    try:
        return await asyncio.wait_for(comm.receive_json_from(), timeout=timeout)
    except Exception:
        return None


async def drain(comm, n=5, timeout=0.5):
    """Drain up to n messages quickly."""
    for _ in range(n):
        if await recv(comm, timeout=timeout) is None:
            break


async def recv_type(comm, wanted_type, max_drain=8, timeout=3):
    """Receive messages until we get one of the wanted type."""
    for _ in range(max_drain):
        m = await recv(comm, timeout=timeout)
        if m is None:
            return None
        if m.get('type') == wanted_type:
            return m
    return None


async def test():
    print("=" * 60)
    print("  Qenagebeya — WebSocket Consumer Tests")
    print("=" * 60)

    # ── Get / create a LIVE stream ─────────────────────────────────────────
    @database_sync_to_async
    def setup_stream():
        from live.models import LiveStream
        from vendors.models import Vendor
        s = LiveStream.objects.filter(status='live').first()
        if not s:
            v = Vendor.objects.filter(status='approved').first()
            if not v:
                return None
            from django.utils import timezone
            s = LiveStream.objects.create(
                vendor=v, title='Test Live 🇪🇹',
                status='live', started_at=timezone.now(),
            )
        return {'pk': s.pk, 'uuid': str(s.stream_id), 'title': s.title}

    info = await setup_stream()
    if not info:
        print("SKIP: No approved vendor — run seed_data.py first.")
        return

    print(f"\n  Stream : {info['title']}")
    print(f"  UUID   : {info['uuid']}")
    path = f"/ws/live/{info['uuid']}/"
    print(f"  WS path: {path}\n")

    passed = []

    # ── T1: Connect ──────────────────────────────────────────────────────────
    comm = WebsocketCommunicator(application, path)
    connected, code = await comm.connect(timeout=8)
    assert connected, f"FAIL T1 — could not connect (code={code})"
    passed.append('T1 Connected')
    print(f"  ✓  T1  Connected")

    # ── T2: History ──────────────────────────────────────────────────────────
    m = await recv_type(comm, 'history', max_drain=3)
    assert m is not None, "FAIL T2 — no history message"
    passed.append('T2 History')
    print(f"  ✓  T2  History ({len(m['messages'])} messages)")

    # Drain all queued system messages (join, viewer_count)
    await drain(comm, n=5, timeout=0.8)

    # ── T3: Chat ─────────────────────────────────────────────────────────────
    await comm.send_json_to({'type': 'chat', 'text': 'Hello from Ethiopia'})
    m = await recv_type(comm, 'chat')
    assert m and 'Hello' in m.get('text', ''), f"FAIL T3 — {m}"
    passed.append('T3 Chat')
    print(f"  ✓  T3  Chat received: {m['text'][:35]}")

    # ── T4: Reaction ─────────────────────────────────────────────────────────
    await comm.send_json_to({'type': 'reaction', 'emoji': '🔥'})
    m = await recv_type(comm, 'reaction')
    assert m and m.get('emoji') == '🔥', f"FAIL T4 — {m}"
    passed.append('T4 Reaction')
    print(f"  ✓  T4  Reaction: {m['emoji']}")

    # ── T5: Question ─────────────────────────────────────────────────────────
    await comm.send_json_to({'type': 'question', 'text': 'How much is it?'})
    m = await recv_type(comm, 'chat')
    assert m and m.get('msg_type') == 'question', f"FAIL T5 — {m}"
    passed.append('T5 Question')
    print(f"  ✓  T5  Question: {m['text'][:35]}")

    # ── T6: Second viewer ────────────────────────────────────────────────────
    comm2 = WebsocketCommunicator(application, path)
    ok2, _ = await comm2.connect(timeout=8)
    assert ok2, "FAIL T6 — second viewer could not connect"
    await drain(comm2, n=6, timeout=0.8)   # drain comm2's welcome messages
    await drain(comm,  n=4, timeout=0.8)   # drain comm1's "viewer joined" msgs

    await comm2.send_json_to({'type': 'chat', 'text': 'Hi from viewer 2!'})
    m = await recv_type(comm, 'chat')      # comm1 should receive viewer2's msg
    assert m and 'viewer 2' in m.get('text', ''), f"FAIL T6 — {m}"
    passed.append('T6 Multi-viewer')
    print(f"  ✓  T6  Multi-viewer: viewer2 → viewer1: {m['text'][:30]}")
    await comm2.disconnect()
    await drain(comm, n=3, timeout=0.8)    # drain "left" + viewer_count

    # ── T7: Viewer count ────────────────────────────────────────────────────
    # After comm2 disconnects, comm1 should have received a viewer_count
    # (already drained above — just check DB)
    @database_sync_to_async
    def check_db():
        from live.models import LiveStream, LiveChat
        s = LiveStream.objects.get(pk=info['pk'])
        msgs = LiveChat.objects.filter(stream_id=info['pk']).count()
        return s.total_views, msgs

    views, db_msgs = await check_db()
    assert db_msgs >= 3, f"FAIL T7 — expected ≥3 DB messages, got {db_msgs}"
    passed.append('T7 DB persistence')
    print(f"  ✓  T7  DB: {views} total views, {db_msgs} messages persisted")

    await comm.disconnect()

    # ── Summary ──────────────────────────────────────────────────────────────
    print()
    print(f"  {len(passed)}/7 tests passed  ✅ ALL GOOD")
    print()
    print("=" * 60)
    print("  WebSocket consumer is fully functional.")
    print()
    print("  Start the server:")
    print("    python manage.py runserver")
    print()
    print(f"  Watch live page:")
    print(f"    http://127.0.0.1:8000/live/{info['uuid']}/")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(test())

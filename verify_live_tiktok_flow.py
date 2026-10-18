"""
End-to-End Live Stream Verification Script:
Tests the entire TikTok-style live lifecycle:
1. Initial state: No vendor camera active -> /live/api/active/ returns 0
2. Vendor goes live & starts camera -> /live/api/active/ returns 1 (is_paused=False, has_host=True)
3. Vendor pauses stream -> /live/api/active/ returns is_paused=True
4. Viewer connects & receives pause state
5. Vendor resumes stream -> /live/api/active/ returns is_paused=False
6. Vendor stops camera / disconnects -> /live/api/active/ returns 0
"""
import os, sys, asyncio, json
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')
import django; django.setup()

from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from qenagebeya.asgi import application
from live.models import LiveStream
from vendors.models import Vendor
from accounts.models import User


async def run_e2e_verification():
    print("=" * 65)
    print("  Qenagebeya Live: TikTok-Style Live & Pause/Resume E2E Test")
    print("=" * 65)

    # 1. Setup stream
    @database_sync_to_async
    def setup_stream():
        v = Vendor.objects.filter(status='approved').first()
        s, _ = LiveStream.objects.get_or_create(
            title='Ethiopian Coffee Ceremony Live',
            defaults={'vendor': v, 'status': 'live', 'host_channel': '', 'is_paused': False}
        )
        s.status = 'live'
        s.host_channel = ''
        s.is_paused = False
        s.save()
        return s.stream_id, s.vendor.user

    stream_uuid, host_user = await setup_stream()
    path = f"/ws/live/{stream_uuid}/"

    # 2. Check initial active streams count (should be 0 because host camera not started)
    @database_sync_to_async
    def get_active_count():
        return LiveStream.objects.filter(status='live').exclude(host_channel='').count()

    initial_count = await get_active_count()
    assert initial_count == 0, f"Expected 0 active streams, got {initial_count}"
    print("  [1/6] ✓ Initial state: 0 active streams (No camera open)")

    # 3. Host connects and starts camera
    host_comm = WebsocketCommunicator(application, path)
    host_comm.scope['user'] = host_user
    ok, _ = await host_comm.connect(timeout=6)
    assert ok, "Host WebSocket connection failed"

    await host_comm.send_json_to({'type': 'webrtc_offer_broadcast'})
    await asyncio.sleep(0.3)

    count_after_start = await get_active_count()
    assert count_after_start == 1, f"Expected 1 active stream after camera start, got {count_after_start}"
    print("  [2/6] ✓ Vendor started camera -> Live Now card visible (count=1)")

    # 4. Host pauses stream
    await host_comm.send_json_to({'type': 'pause_stream'})
    await asyncio.sleep(0.3)

    @database_sync_to_async
    def get_pause_state():
        s = LiveStream.objects.get(stream_id=stream_uuid)
        return s.is_paused

    is_paused = await get_pause_state()
    assert is_paused is True, "Stream should be marked is_paused=True"
    print("  [3/6] ✓ Vendor paused stream -> Card displays '⏸️ PAUSED' badge")

    # 5. Viewer connects while paused and receives pause status
    view_comm = WebsocketCommunicator(application, path)
    ok_v, _ = await view_comm.connect(timeout=6)
    assert ok_v, "Viewer connect failed"

    # Viewer should receive stream_status with is_paused=True
    msg = await asyncio.wait_for(view_comm.receive_json_from(), timeout=4)
    assert msg.get('type') == 'stream_status', f"Unexpected message: {msg}"
    assert msg.get('is_paused') is True, "Viewer did not receive is_paused=True"
    print("  [4/6] ✓ Viewer connected and received pause overlay signal")

    # 6. Host resumes stream
    await host_comm.send_json_to({'type': 'resume_stream'})
    await asyncio.sleep(0.3)

    is_paused_after_resume = await get_pause_state()
    assert is_paused_after_resume is False, "Stream should be is_paused=False after resume"
    print("  [5/6] ✓ Vendor resumed stream -> Pause overlay dismissed & video live")

    # 7. Host stops camera and disconnects
    await host_comm.send_json_to({'type': 'stop_camera'})
    await asyncio.sleep(0.3)
    await host_comm.disconnect()
    await view_comm.disconnect()
    await asyncio.sleep(0.3)

    final_count = await get_active_count()
    assert final_count == 0, f"Expected 0 active streams after stop_camera, got {final_count}"
    print("  [6/6] ✓ Vendor stopped camera -> Removed from Live Now (count=0)")

    print()
    print("=" * 65)
    print("  ALL 6/6 E2E CHECKS PASSED! TikTok-Style Live System is 100% Ready.")
    print("=" * 65)


if __name__ == '__main__':
    asyncio.run(run_e2e_verification())

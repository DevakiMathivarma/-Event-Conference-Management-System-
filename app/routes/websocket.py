import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.utils.logger import logger

router = APIRouter(tags=["WebSocket - Live Check-In Updates"])


class ConnectionManager:

    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}
        self.loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop

    async def connect(self, event_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.setdefault(event_id, []).append(websocket)

    def disconnect(self, event_id: int, websocket: WebSocket) -> None:
        if event_id in self.active_connections:
            if websocket in self.active_connections[event_id]:
                self.active_connections[event_id].remove(websocket)
            if not self.active_connections[event_id]:
                del self.active_connections[event_id]

    async def broadcast(self, event_id: int, message: dict) -> None:
        for connection in self.active_connections.get(event_id, []):
            try:
                await connection.send_json(message)
            except Exception as error:
                logger.error(f"WebSocket send failed : {str(error)}")


manager = ConnectionManager()


# organizers/staff watching their own event's check-in desk live - keyed
# by event_id, so multiple people monitoring the same event all see the
# same live count update together
@router.websocket("/ws/events/{event_id}/check-ins")
async def check_in_live_updates(websocket: WebSocket, event_id: int):
    await manager.connect(event_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(event_id, websocket)


# called from synchronous service functions - hands the broadcast off
# to the real event loop safely, same proven fix carried forward from
# every previous project's websocket feature
def broadcast_check_in_update_sync(event_id: int, message: dict) -> None:

    if manager.loop is None:
        logger.error("WebSocket broadcast skipped : event loop not yet available.")
        return

    try:
        asyncio.run_coroutine_threadsafe(manager.broadcast(event_id, message), manager.loop)
    except Exception as error:
        logger.error(f"WebSocket broadcast failed : {str(error)}")
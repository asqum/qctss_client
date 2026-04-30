"""
WebSocket manager for real-time job status monitoring
"""
import json
import logging
import threading
import time
from typing import Optional, Callable, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode
import websocket

from .exceptions import WebSocketError, WebSocketConnectionError, WebSocketAuthError
from .models import WebSocketMessage, JobStatus

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for job status monitoring
    """
    
    def __init__(self):
        self._connections: Dict[int, websocket.WebSocketApp] = {}
        self._callbacks: Dict[int, Callable[[JobStatus], None]] = {}
        self._error_callbacks: Dict[int, Callable[[Exception], None]] = {}
        self._threads: Dict[int, threading.Thread] = {}
        self._running: Dict[int, bool] = {}
    
    def connect(
        self,
        job_id: int,
        websocket_url: str,
        token: str,
        callback: Callable[[JobStatus], None],
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """
        Establish WebSocket connection for job monitoring
        
        Args:
            job_id: Job ID to monitor
            websocket_url: WebSocket server URL  
            token: Authentication token
            callback: Function called with job status updates
            on_error: Optional error handler
            
        Raises:
            WebSocketConnectionError: Connection failed
            WebSocketAuthError: Authentication failed
        """
        if job_id in self._connections:
            logger.warning(f"Job {job_id} already has active connection")
            return
        
        self._callbacks[job_id] = callback
        self._error_callbacks[job_id] = on_error or (lambda e: logger.error(f"WebSocket error: {e}"))
        self._running[job_id] = True
        
        # Create WebSocket URL with token parameter
        # According to 2026-01-07 spec: Use token parameter instead of message-based auth
        base_url = f"{websocket_url}/ws/job/{job_id}"
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)
        query_params['token'] = [token]
        new_query = urlencode(query_params, doseq=True)
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
        
        logger.info(f"Connecting to WebSocket: {url}")
        
        def on_open(ws):
            logger.info(f"WebSocket connected for job {job_id}")
            # Authentication now handled via URL parameter (token)
            # No need to send AuthMessage per 2026-01-07 specification
        
        def on_message(ws, message):
            try:
                logger.info(f"[WS_RAW_MESSAGE] job {job_id}: {message[:100]}")
                data = json.loads(message)
                ws_msg = WebSocketMessage(**data)
                self._handle_message(job_id, ws_msg)
            except Exception as e:
                logger.error(f"Error processing message for job {job_id}: {e}")
                if job_id in self._error_callbacks:
                    self._error_callbacks[job_id](WebSocketError(f"Message processing error: {e}"))
        
        def on_error(ws, error):
            logger.error(f"WebSocket error for job {job_id}: {error}")
            self._error_callbacks[job_id](WebSocketConnectionError(f"Connection error: {error}"))
        
        def on_close(ws, close_status_code, close_msg):
            logger.info(f"WebSocket closed for job {job_id}: {close_status_code}")
            self._cleanup_connection(job_id)
        
        # Create WebSocket connection
        ws = websocket.WebSocketApp(
            url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        
        self._connections[job_id] = ws
        
        # Start connection in separate thread
        def run_websocket():
            try:
                ws.run_forever(ping_interval=30, ping_timeout=10)
            except Exception as e:
                logger.error(f"WebSocket thread error for job {job_id}: {e}")
                self._error_callbacks[job_id](WebSocketConnectionError(f"Thread error: {e}"))
        
        thread = threading.Thread(target=run_websocket, daemon=True)
        self._threads[job_id] = thread
        thread.start()
    
    def disconnect(self, job_id: int) -> None:
        """
        Disconnect WebSocket for specific job
        
        Args:
            job_id: Job ID to disconnect
        """
        if job_id not in self._connections:
            return
        
        logger.info(f"Disconnecting WebSocket for job {job_id}")
        
        # Mark as not running
        self._running[job_id] = False
        
        # Close WebSocket connection
        ws = self._connections[job_id]
        if ws:
            ws.close()
        
        # Wait for thread to finish (but avoid joining if we're in the worker thread)
        thread = self._threads.get(job_id)
        if thread and thread.is_alive():
            # Don't join if we're being called from the same thread
            current_thread = threading.current_thread()
            if thread != current_thread:
                try:
                    thread.join(timeout=5.0)
                except RuntimeError as e:
                    if "cannot join current thread" in str(e):
                        logger.debug(f"Cannot join WebSocket thread from itself for job {job_id}")
                    else:
                        raise
            else:
                # We're in the WebSocket thread, just mark for cleanup
                logger.debug(f"Disconnect called from WebSocket thread for job {job_id}, skipping join")
        
        self._cleanup_connection(job_id)
    
    def disconnect_all(self) -> None:
        """Disconnect all WebSocket connections"""
        job_ids = list(self._connections.keys())
        for job_id in job_ids:
            self.disconnect(job_id)
    
    def _handle_message(self, job_id: int, message: WebSocketMessage) -> None:
        """
        Handle incoming WebSocket message
        
        Args:
            job_id: Job ID
            message: WebSocket message
        """
        logger.info(f"[WS_RECEIVED] job {job_id} message: {message.type}")
        
        if message.type == "error":
            error = WebSocketError(
                message.message or "WebSocket error",
                error_code=message.code,
                details={"job_id": job_id}
            )
            
            # Handle authentication errors specifically
            if message.code in ["unauthorized", "invalid_token", "auth_timeout"]:
                error = WebSocketAuthError(
                    message.message or "Authentication failed",
                    error_code=message.code,
                    details={"job_id": job_id}
                )
            
            self._error_callbacks[job_id](error)
            
            # Close connection on terminal errors
            if message.code in ["unauthorized", "job_not_found", "invalid_token"]:
                self.disconnect(job_id)
            
            return
        
        if message.type in ["status_update", "initial_status"]:
            job_status = message.to_job_status()
            if job_status:
                logger.info(f"[WS_CALLBACK] Calling status callback for job {job_id}, status: {job_status.status}")
                self._callbacks[job_id](job_status)
                
                # Auto-disconnect if job reaches terminal state
                if job_status.is_terminal:
                    logger.info(f"Job {job_id} reached terminal state, disconnecting")
                    self.disconnect(job_id)
            return
        
        if message.type == "auth_required":
            logger.info(f"Auth required for job {job_id}")
            return
        
        if message.type == "subscribed":
            logger.debug(f"Job {job_id} subscription confirmed")
            return
        
        logger.warning(f"Unknown message type for job {job_id}: {message.type}")
    
    def _cleanup_connection(self, job_id: int) -> None:
        """Clean up connection resources"""
        self._connections.pop(job_id, None)
        self._callbacks.pop(job_id, None)
        self._error_callbacks.pop(job_id, None)
        self._threads.pop(job_id, None)
        self._running.pop(job_id, None)
    
    def is_connected(self, job_id: int) -> bool:
        """Check if job has active WebSocket connection"""
        return job_id in self._connections and self._running.get(job_id, False)
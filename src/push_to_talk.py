"""Push-to-talk keyboard listener.

Detects when the user holds/releases the configured key (spacebar by default)
to trigger audio recording. Thread-safe state management with debounce.
"""

import threading
import time
from pynput import keyboard


class PushToTalk:
    """Listens for key press/release events to control recording.

    Uses pynput's GlobalListener to detect key events system-wide,
    allowing the user to hold a key to record and release to stop.

    Attributes:
        trigger_key: The key that triggers recording (default: space).
        _is_holding: Thread-safe flag for current key state.
        _last_release: Timestamp of last key release (debounce).
        _debounce_seconds: Minimum time between triggers.
        _on_press: Callback fired when trigger key is pressed.
        _on_release: Callback fired when trigger key is released.
        _listener: The pynput keyboard listener instance.
    """

    def __init__(
        self,
        trigger_key=None,
        on_press=None,
        on_release=None,
        debounce_seconds=0.3,
    ):
        """Initialize the push-to-talk listener.

        Args:
            trigger_key: The key to use for push-to-talk.
                         Default is keyboard.Key.space (spacebar).
            on_press: Callback function(key) called when key is pressed.
            on_release: Callback function(key) called when key is released.
            debounce_seconds: Minimum seconds between consecutive triggers
                            to prevent accidental double-fires.
        """
        self.trigger_key = trigger_key or keyboard.Key.space
        self._is_holding = False
        self._last_release = 0
        self._debounce_seconds = debounce_seconds
        self._on_press = on_press
        self._on_release = on_release
        self._listener = None
        self._lock = threading.Lock()

    def _can_trigger(self):
        """Check if enough time has passed since last release for debounce.

        Returns:
            True if debounce period has elapsed, False otherwise.
        """
        now = time.time()
        if now - self._last_release < self._debounce_seconds:
            return False
        return True

    def _on_key_event(self, key, is_press):
        """Internal handler for all keyboard events.

        Filters for the trigger key and manages state transitions
        between idle and recording states. Callbacks are invoked
        outside the lock to avoid blocking key events during slow
        operations like transcription.

        Args:
            key: The key that generated the event.
            is_press: True for press events, False for release events.
        """
        callback = None
        try:
            if key == self.trigger_key:
                with self._lock:
                    if is_press:
                        if not self._is_holding and self._can_trigger():
                            self._is_holding = True
                            callback = self._on_press
                    else:
                        if self._is_holding:
                            self._is_holding = False
                            self._last_release = time.time()
                            callback = self._on_release
        except AttributeError:
            # Some keys don't have the same attributes, safe to ignore
            pass

        if callback:
            callback(key)

    def on_press(self, key):
        """Public wrapper for press events."""
        self._on_key_event(key, is_press=True)

    def on_release(self, key):
        """Public wrapper for release events."""
        self._on_key_event(key, is_press=False)

    @property
    def is_holding(self):
        """Check if the trigger key is currently being held.

        Returns:
            True if the user is holding the trigger key, False otherwise.
        """
        with self._lock:
            return self._is_holding

    def start(self):
        """Start the keyboard listener in a daemon thread.

        The listener runs in the background and calls callbacks
        when the trigger key is pressed or released.
        """
        self._listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release,
            suppress=False,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        """Stop the keyboard listener and clean up resources."""
        if self._listener:
            self._listener.stop()
            self._listener = None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        return False

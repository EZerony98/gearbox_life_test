"""CSV 数据写入后台任务。"""

from PySide6.QtCore import QObject, Signal, Slot

from services.data_service import DataService


class DataWriterWorker(QObject):
    session_started = Signal(str)
    session_stopped = Signal()
    error = Signal(str)

    def __init__(self, service: DataService) -> None:
        super().__init__()
        self.service = service
        self._failed = False

    @Slot(dict)
    def start_session(self, metadata: dict) -> None:
        try:
            path = self.service.start_session(metadata)
            self.session_started.emit(str(path))
        except Exception as error:
            self._report_error(error)

    @Slot(dict)
    def write_sample(self, sample: dict) -> None:
        if self._failed:
            return
        try:
            self.service.write_sample(sample)
        except Exception as error:
            self._report_error(error)

    @Slot(str, str, str)
    def write_event(self, source: str, message: str, level: str) -> None:
        if self._failed:
            return
        try:
            self.service.write_event(source, message, level)
        except Exception as error:
            self._report_error(error)

    @Slot()
    def stop_session(self) -> None:
        try:
            self.service.stop_session("stopped")
        except Exception as error:
            self._report_error(error)
        finally:
            self.session_stopped.emit()

    def _report_error(self, error: Exception) -> None:
        self._failed = True
        self.error.emit(str(error))


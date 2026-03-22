"""Background QThread worker for the summarization pipeline."""
from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from ytb_summarizer.transcript import get_video_info, fetch_transcript
from ytb_summarizer.templates import get_template, render_prompt
from ytb_summarizer.summarizer import summarize
from ytb_summarizer.output import save_summary
from ytb_gui import config as cfg


class SummarizeWorker(QThread):
    progress = Signal(str)       # log line
    progress_pct = Signal(int)   # 0-100
    finished = Signal(str, str)  # (markdown_content, output_path)
    error = Signal(str)

    def __init__(
        self,
        url: str,
        provider_config: dict,
        template_name: str,
        output_dir: str,
        transcript_lang: str = "en",
        parent=None,
    ):
        super().__init__(parent)
        self.url = url
        self.provider_config = provider_config
        self.template_name = template_name
        self.output_dir = output_dir
        self.transcript_lang = transcript_lang
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _log(self, msg: str):
        self.progress.emit(msg)

    def run(self):
        try:
            # Step 1: Get video info
            self._log("⏳ 正在获取视频信息...")
            self.progress_pct.emit(10)
            info = get_video_info(self.url)
            title = info["title"]
            self._log(f"✓ 视频标题: {title}")
            self.progress_pct.emit(25)

            if self._cancelled:
                return

            # Step 2: Fetch transcript
            self._log(f"⏳ 正在提取字幕 (语言: {self.transcript_lang})...")
            transcript = fetch_transcript(self.url, lang=self.transcript_lang)
            word_count = len(transcript.split())
            self._log(f"✓ 字幕提取完成 ({word_count} 词)")
            self.progress_pct.emit(50)

            if self._cancelled:
                return

            # Step 3: Load template and build prompt
            self._log(f"⏳ 加载模板: {self.template_name}")
            template = get_template(
                self.template_name,
                custom_dir=cfg.templates_dir(),
            )
            prompt = render_prompt(template, title, self.url, transcript)
            self.progress_pct.emit(60)

            if self._cancelled:
                return

            # Step 4: Call LLM
            self._log(f"● 正在调用 {self.provider_config['provider']} LLM...")
            content = summarize(
                transcript=transcript,
                title=title,
                url=self.url,
                prompt=prompt,
                provider_config=self.provider_config,
                progress_cb=self._log,
            )
            self._log("✓ LLM 响应完成")
            self.progress_pct.emit(85)

            if self._cancelled:
                return

            # Step 5: Save file
            self._log("⏳ 保存文件...")
            output_path = save_summary(content, title, self.output_dir)
            self._log(f"✓ 已保存到: {output_path}")
            self.progress_pct.emit(100)

            self.finished.emit(content, str(output_path))

        except Exception as e:
            self.error.emit(str(e))

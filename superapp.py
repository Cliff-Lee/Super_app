#!/usr/bin/env python3
import os
import subprocess
import threading
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# ---------------------------
# Additional libraries (from supperapp.py)
# ---------------------------
from PIL import Image, ImageTk
import pytesseract
import PyPDF2
from argostranslate import translate, package
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import letter
from pdf2image import convert_from_path
import whisper

# =====================================================
# Tab 1: Media Converter (from supperapp.py)
# =====================================================
class MediaConverterTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.create_widgets()
    
    def create_widgets(self):
        # Input file selection
        tk.Label(self, text="Input File:").pack(pady=(20,5))
        self.input_entry = tk.Entry(self, width=60)
        self.input_entry.pack(pady=5)
        tk.Button(self, text="Browse", command=self.browse_file).pack(pady=5)

        # Output format selection
        tk.Label(self, text="Output Format:").pack(pady=5)
        self.format_options = ["mp4", "mp3", "avi", "mkv", "mov", "webm", "wav", "flac", "aac", "ogg"]
        self.format_var = tk.StringVar()
        self.format_combobox = ttk.Combobox(self, textvariable=self.format_var, values=self.format_options, state="readonly")
        self.format_combobox.current(0)  # default to mp4
        self.format_combobox.pack(pady=5)

        # Output file selection
        tk.Label(self, text="Output File:").pack(pady=5)
        self.output_entry = tk.Entry(self, width=60)
        self.output_entry.pack(pady=5)
        tk.Button(self, text="Browse", command=self.browse_output_file).pack(pady=5)

        # Convert button
        tk.Button(self, text="Convert", command=self.convert).pack(pady=20)
    
    def browse_file(self):
        filename = filedialog.askopenfilename(title="Select Input File")
        if filename:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filename)
            # Auto-fill output filename if empty
            if not self.output_entry.get():
                base, _ = os.path.splitext(filename)
                self.output_entry.insert(0, base + "." + self.format_var.get())

    def browse_output_file(self):
        ext = self.format_var.get()
        filetypes = [(f"{ext.upper()} Files", f"*.{ext}"), ("All Files", "*.*")]
        filename = filedialog.asksaveasfilename(title="Select Output File", filetypes=filetypes, defaultextension="." + ext)
        if filename:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filename)

    def convert(self):
        input_file = self.input_entry.get()
        output_file = self.output_entry.get()
        if not input_file or not os.path.isfile(input_file):
            messagebox.showerror("Error", "Invalid input file.")
            return
        if not output_file:
            messagebox.showerror("Error", "Please specify an output file.")
            return
        
        # Determine if input is audio and output is video so we can add a dummy video track if needed.
        audio_exts = [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"]
        video_exts = [".mp4", ".avi", ".mkv", ".mov", ".webm"]
        input_ext = os.path.splitext(input_file)[1].lower()
        output_ext = os.path.splitext(output_file)[1].lower()

        if input_ext in audio_exts and output_ext in video_exts:
            command = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "color=c=black:s=640x480:r=25",
                "-i", input_file,
                "-shortest",
                "-c:v", "libx264",
                "-c:a", "aac",
                output_file
            ]
        else:
            command = ["ffmpeg", "-y", "-i", input_file, output_file]
        
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                messagebox.showinfo("Success", "Conversion completed successfully.")
            else:
                error_message = stderr.decode("utf-8")
                messagebox.showerror("Error", f"Conversion failed.\n{error_message}")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

# =====================================================
# Tab 2: Offline Translator (from supperapp.py)
# =====================================================
class OfflineTranslatorTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.languages = [
            "en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko",
            "ar", "hi", "nl", "sv", "pl", "tr"
        ]
        self.create_widgets()
    
    def create_widgets(self):
        # Input text area
        frame_text = ttk.LabelFrame(self, text="Input Text")
        frame_text.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.text_input = tk.Text(frame_text, width=60, height=10)
        self.text_input.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame_text, command=self.text_input.yview)
        scrollbar.pack(side="right", fill="y")
        self.text_input.config(yscrollcommand=scrollbar.set)

        # Load text file button
        btn_load = ttk.Button(self, text="Load Text File", command=self.select_file)
        btn_load.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        # Language selection dropdowns; defaults: from Chinese to English.
        frame_lang = ttk.Frame(self)
        frame_lang.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        ttk.Label(frame_lang, text="From:").grid(row=0, column=0, padx=5, pady=5)
        self.from_lang_combo = ttk.Combobox(frame_lang, values=self.languages, state="readonly", width=5)
        from_default_index = self.languages.index("zh") if "zh" in self.languages else 0
        self.from_lang_combo.current(from_default_index)
        self.from_lang_combo.grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(frame_lang, text="To:").grid(row=0, column=2, padx=5, pady=5)
        self.to_lang_combo = ttk.Combobox(frame_lang, values=self.languages, state="readonly", width=5)
        to_default_index = self.languages.index("en") if "en" in self.languages else 0
        self.to_lang_combo.current(to_default_index)
        self.to_lang_combo.grid(row=0, column=3, padx=5, pady=5)

        # Translate button
        btn_translate = ttk.Button(self, text="Translate", command=self.translate_action)
        btn_translate.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        # Output area for translated text
        frame_result = ttk.LabelFrame(self, text="Translated Text")
        frame_result.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
        self.result_text = tk.Text(frame_result, width=60, height=10)
        self.result_text.pack(side="left", fill="both", expand=True)
        scrollbar2 = ttk.Scrollbar(frame_result, command=self.result_text.yview)
        scrollbar2.pack(side="right", fill="y")
        self.result_text.config(yscrollcommand=scrollbar2.set)

        # Configure grid weights for resizing.
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
    
    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert(tk.END, f.read())
    
    def translate_text(self, text, from_lang_code, to_lang_code):
        installed_languages = translate.load_installed_languages()
        from_lang = next((lang for lang in installed_languages if lang.code == from_lang_code), None)
        to_lang = next((lang for lang in installed_languages if lang.code == to_lang_code), None)
        if not from_lang or not to_lang:
            raise Exception("Language package not installed. Install the package for your selected language pair.")
        translation = from_lang.get_translation(to_lang)
        return translation.translate(text)
    
    def translate_action(self):
        try:
            from_lang = self.from_lang_combo.get()
            to_lang = self.to_lang_combo.get()
            text = self.text_input.get("1.0", tk.END)
            if not text.strip():
                messagebox.showwarning("Warning", "No text found to translate.")
                return
            result = self.translate_text(text, from_lang, to_lang)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, result)
        except Exception as e:
            messagebox.showerror("Error", str(e))

# =====================================================
# Tab 3: PDF Translator (from supperapp.py)
# =====================================================
class PDFTranslatorTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.input_pdf_path = None
        self.output_pdf_path = "translated.pdf"
        self.original_current_page = 1
        self.original_total_pages = 0
        self.translated_current_page = 1
        self.translated_total_pages = 0
        self.language_options = {}
        self.install_required_language_pairs()  # Install language packages first
        self.create_widgets()                     # Then create widgets

    def get_pdf_preview_image(self, pdf_path, page_number=1):
        try:
            images = convert_from_path(pdf_path, dpi=100, first_page=page_number, last_page=page_number)
            if images:
                return images[0]
            else:
                raise Exception("No pages found in PDF.")
        except Exception as e:
            raise Exception("Error generating preview image: " + str(e))
    
    def install_required_language_pairs(self):
        try:
            package.update_package_index()
            available_packages = package.get_available_packages()
            required_pairs = [
                ('ko','en'), ('en','ko'),
                ('de','en'), ('en','de'),
                ('zh','en'), ('en','zh'),
                ('es','en'), ('en','es')
            ]
            installed_langs = translate.get_installed_languages()

            def is_pair_installed(src, tgt, installed_langs):
                for lang in installed_langs:
                    if lang.code == src:
                        for trans in lang.translations_to:
                            if trans.to_lang.code == tgt:
                                return True
                return False

            for src, tgt in required_pairs:
                if not is_pair_installed(src, tgt, installed_langs):
                    found_package = None
                    for pkg in available_packages:
                        if pkg.from_code == src and pkg.to_code == tgt:
                            found_package = pkg
                            break
                    if found_package:
                        pkg_path = found_package.download()
                        package.install_from_path(pkg_path)
                        installed_langs = translate.get_installed_languages()
        except Exception as e:
            messagebox.showerror("Error", f"Language package installation error: {e}")
        
        # Build language options from installed languages.
        for lang in translate.get_installed_languages():
            name = getattr(lang, "name", lang.code)
            display = f"{name} ({lang.code})"
            self.language_options[display] = lang.code

    def create_widgets(self):
        # Top control frame
        control_frame = tk.Frame(self)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # File selection for PDF
        self.select_button = tk.Button(control_frame, text="Select Input PDF", command=self.select_pdf)
        self.select_button.grid(row=0, column=0, padx=5, pady=5)
        self.pdf_label = tk.Label(control_frame, text="No file selected")
        self.pdf_label.grid(row=0, column=1, padx=5, pady=5)

        # Language selection
        tk.Label(control_frame, text="Source Language:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        tk.Label(control_frame, text="Target Language:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        language_list = list(self.language_options.keys()) if self.language_options else []
        self.source_lang_combo = ttk.Combobox(control_frame, values=language_list, state="readonly")
        self.source_lang_combo.grid(row=1, column=1, padx=5, pady=5)
        if language_list:
            self.source_lang_combo.current(0)
        self.target_lang_combo = ttk.Combobox(control_frame, values=language_list, state="readonly")
        self.target_lang_combo.grid(row=2, column=1, padx=5, pady=5)
        if len(language_list) > 1:
            self.target_lang_combo.current(1)
        else:
            self.target_lang_combo.current(0)

        # Translate button
        self.translate_button = tk.Button(control_frame, text="Translate PDF", command=self.translate_pdf)
        self.translate_button.grid(row=3, column=0, columnspan=2, padx=5, pady=10)

        # Progress bar
        self.progress_bar = ttk.Progressbar(control_frame, orient="horizontal", length=300, mode="determinate", maximum=100)
        self.progress_bar.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

        # Save button
        self.save_button = tk.Button(control_frame, text="Save Translated PDF", command=self.save_translated_pdf, state=tk.DISABLED)
        self.save_button.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

        # Preview frame for original and translated PDFs
        preview_frame = tk.Frame(self)
        preview_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Original PDF preview
        self.original_preview_frame = tk.LabelFrame(preview_frame, text="Original PDF Preview")
        self.original_preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.original_canvas = tk.Canvas(self.original_preview_frame, bg="gray")
        self.original_canvas.pack(fill=tk.BOTH, expand=True)
        nav_frame_orig = tk.Frame(self.original_preview_frame)
        nav_frame_orig.pack(fill=tk.X)
        self.prev_orig_button = tk.Button(nav_frame_orig, text="Previous", command=self.prev_original_page, state=tk.DISABLED)
        self.prev_orig_button.pack(side=tk.LEFT, padx=5, pady=2)
        self.orig_page_label = tk.Label(nav_frame_orig, text="Page 0 of 0")
        self.orig_page_label.pack(side=tk.LEFT, padx=5)
        self.next_orig_button = tk.Button(nav_frame_orig, text="Next", command=self.next_original_page, state=tk.DISABLED)
        self.next_orig_button.pack(side=tk.LEFT, padx=5, pady=2)

        # Translated PDF preview
        self.translated_preview_frame = tk.LabelFrame(preview_frame, text="Translated PDF Preview")
        self.translated_preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.translated_canvas = tk.Canvas(self.translated_preview_frame, bg="gray")
        self.translated_canvas.pack(fill=tk.BOTH, expand=True)
        nav_frame_trans = tk.Frame(self.translated_preview_frame)
        nav_frame_trans.pack(fill=tk.X)
        self.prev_trans_button = tk.Button(nav_frame_trans, text="Previous", command=self.prev_translated_page, state=tk.DISABLED)
        self.prev_trans_button.pack(side=tk.LEFT, padx=5, pady=2)
        self.trans_page_label = tk.Label(nav_frame_trans, text="Page 0 of 0")
        self.trans_page_label.pack(side=tk.LEFT, padx=5)
        self.next_trans_button = tk.Button(nav_frame_trans, text="Next", command=self.next_translated_page, state=tk.DISABLED)
        self.next_trans_button.pack(side=tk.LEFT, padx=5, pady=2)

    def update_progress(self, value):
        self.progress_bar.config(value=value)
    
    def select_pdf(self):
        file_path = filedialog.askopenfilename(title="Select PDF File", filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.input_pdf_path = file_path
            self.pdf_label.config(text=os.path.basename(file_path))
            try:
                with open(self.input_pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    self.original_total_pages = len(reader.pages)
            except Exception as e:
                messagebox.showerror("Error", "Failed to read PDF: " + str(e))
                return
            if self.original_total_pages > 1:
                self.prev_orig_button.config(state=tk.NORMAL)
                self.next_orig_button.config(state=tk.NORMAL)
            else:
                self.prev_orig_button.config(state=tk.DISABLED)
                self.next_orig_button.config(state=tk.DISABLED)
            self.original_current_page = 1
            self.display_original_preview(self.original_current_page)
    
    def display_original_preview(self, page):
        try:
            img = self.get_pdf_preview_image(self.input_pdf_path, page_number=page)
            self.original_image_tk = ImageTk.PhotoImage(img)
            self.original_canvas.delete("all")
            self.original_canvas.create_image(0, 0, anchor="nw", image=self.original_image_tk)
            self.orig_page_label.config(text=f"Page {page} of {self.original_total_pages}")
        except Exception as e:
            messagebox.showerror("Error", "Original preview: " + str(e))
    
    def display_translated_preview(self, page):
        try:
            img = self.get_pdf_preview_image(self.output_pdf_path, page_number=page)
            self.translated_image_tk = ImageTk.PhotoImage(img)
            self.translated_canvas.delete("all")
            self.translated_canvas.create_image(0, 0, anchor="nw", image=self.translated_image_tk)
            self.trans_page_label.config(text=f"Page {page} of {self.translated_total_pages}")
        except Exception as e:
            messagebox.showerror("Error", "Translated preview: " + str(e))
    
    def prev_original_page(self):
        if self.original_current_page > 1:
            self.original_current_page -= 1
            self.display_original_preview(self.original_current_page)
    
    def next_original_page(self):
        if self.original_current_page < self.original_total_pages:
            self.original_current_page += 1
            self.display_original_preview(self.original_current_page)
    
    def prev_translated_page(self):
        if self.translated_current_page > 1:
            self.translated_current_page -= 1
            self.display_translated_preview(self.translated_current_page)
    
    def next_translated_page(self):
        if self.translated_current_page < self.translated_total_pages:
            self.translated_current_page += 1
            self.display_translated_preview(self.translated_current_page)
    
    def save_translated_pdf(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if save_path:
            try:
                shutil.copy(self.output_pdf_path, save_path)
                messagebox.showinfo("Saved", f"Translated PDF saved to {save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save PDF: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_path, progress_callback=None):
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                num_pages = len(reader.pages)
                for i, page in enumerate(reader.pages, start=1):
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text += page_text + "\n"
                    else:
                        try:
                            images = convert_from_path(pdf_path, dpi=200, first_page=i, last_page=i)
                            if images:
                                ocr_text = pytesseract.image_to_string(images[0])
                                text += ocr_text + "\n"
                        except Exception as ocr_e:
                            raise Exception(f"Error during OCR on page {i}: {ocr_e}")
                    if progress_callback:
                        progress_callback((i / num_pages) * 50)
        except Exception as e:
            raise Exception("Error extracting text from PDF: " + str(e))
        if not text.strip():
            raise Exception("No text could be extracted from the PDF.")
        return text
    
    def translate_text(self, text, from_lang_code, to_lang_code):
        try:
            installed_languages = translate.get_installed_languages()
            from_lang_obj = next((lang for lang in installed_languages if lang.code == from_lang_code), None)
            to_lang_obj = next((lang for lang in installed_languages if lang.code == to_lang_code), None)
            if not from_lang_obj or not to_lang_obj:
                raise Exception("Translation packages for the selected language pair are not installed.")
            translation = from_lang_obj.get_translation(to_lang_obj)
            return translation.translate(text)
        except Exception as e:
            raise Exception("Error during translation: " + str(e))
    
    def create_translated_pdf(self, text, output_pdf_path):
        try:
            doc = SimpleDocTemplate(output_pdf_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            paragraphs = text.split('\n\n')
            for para in paragraphs:
                para = para.replace('\n', ' ')
                if para.strip():
                    story.append(Paragraph(para.strip(), styles["Normal"]))
                    story.append(Spacer(1, 12))
            doc.build(story)
        except Exception as e:
            raise Exception("Error creating translated PDF: " + str(e))
    
    def translate_pdf(self):
        if not self.input_pdf_path:
            messagebox.showerror("Error", "Please select an input PDF file.")
            return

        source_lang_display = self.source_lang_combo.get()
        target_lang_display = self.target_lang_combo.get()
        source_lang = self.language_options.get(source_lang_display)
        target_lang = self.language_options.get(target_lang_display)

        self.translate_button.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED)
        self.update_progress(0)

        def process_translation():
            try:
                extracted_text = self.extract_text_from_pdf(self.input_pdf_path, progress_callback=self.update_progress)
                self.update_progress(50)
                translated_text = self.translate_text(extracted_text, source_lang, target_lang)
                self.update_progress(75)
                self.create_translated_pdf(translated_text, self.output_pdf_path)
                self.update_progress(100)
                self.after(0, lambda: messagebox.showinfo("Success", f"Translated PDF saved as {self.output_pdf_path}"))
                try:
                    with open(self.output_pdf_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        self.translated_total_pages = len(reader.pages)
                except Exception:
                    self.translated_total_pages = 1
                self.translated_current_page = 1
                self.after(0, self.display_translated_preview, self.translated_current_page)
                if self.translated_total_pages > 1:
                    self.after(0, lambda: self.prev_trans_button.config(state=tk.NORMAL))
                    self.after(0, lambda: self.next_trans_button.config(state=tk.NORMAL))
                else:
                    self.after(0, lambda: self.prev_trans_button.config(state=tk.DISABLED))
                    self.after(0, lambda: self.next_trans_button.config(state=tk.DISABLED))
                self.after(0, lambda: self.save_button.config(state=tk.NORMAL))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.update_progress(0)
            finally:
                self.after(0, lambda: self.translate_button.config(state=tk.NORMAL))
        
        threading.Thread(target=process_translation).start()

# =====================================================
# Tab 4: Video Translator (from supperapp.py)
# =====================================================
class VideoTranslatorTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.languages = {
            "English": "en",
            "Chinese": "zh",
            "Russian": "ru",
            "Spanish": "es",
            "French": "fr",
            "German": "de",
            "Japanese": "ja",
            "Korean": "ko",
            "Lithuanian": "lt",
            "Italian": "it",
            "Portuguese": "pt",
            "Turkish": "tr",
            "Dutch": "nl",
            "Arabic": "ar",
            "Swedish": "sv",
            "Hindi": "hi",
            "Polish": "pl",
            "Danish": "da",
            "Finnish": "fi",
            "Czech": "cs",
            "Greek": "el"
        }
        self.create_widgets()
    
    def create_widgets(self):
        # File selection
        tk.Label(self, text="Input File:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.file_entry = tk.Entry(self, width=50)
        self.file_entry.grid(row=0, column=1, padx=5, pady=5)
        tk.Button(self, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=5, pady=5)

        # Language selection
        tk.Label(self, text="Source Language:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.language_var = tk.StringVar()
        self.language_combobox = ttk.Combobox(self, textvariable=self.language_var, state="readonly")
        self.language_combobox['values'] = list(self.languages.keys())
        self.language_combobox.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.language_combobox.current(0)

        # Start button
        tk.Button(self, text="Start Translation", command=self.start_transcription_wrapper).grid(row=2, column=1, padx=5, pady=15)

        # Status label
        self.status_label = tk.Label(self, text="Ready", fg="blue")
        self.status_label.grid(row=3, column=0, columnspan=3, padx=5, pady=5)
    
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select video or audio file",
            filetypes=[("Media files", "*.mp4 *.mp3 *.mkv *.wav"), ("All files", "*.*")]
        )
        if filename:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, filename)
    
    def save_file_dialog(self):
        return filedialog.asksaveasfilename(
            defaultextension=".srt",
            filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
        )
    
    def format_time(self, seconds):
        msec = int((seconds - int(seconds)) * 1000)
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d},{msec:03d}"
    
    def get_language_code(self):
        selected = self.language_var.get()
        return self.languages.get(selected, selected)
    
    def start_transcription(self):
        input_file = self.file_entry.get()
        if not input_file:
            messagebox.showerror("Error", "Please select an input file.")
            return

        language = self.get_language_code()
        if language == "":
            messagebox.showerror("Error", "Please select the language.")
            return

        try:
            self.status_label.config(text="Loading model...")
            self.update_idletasks()
            model = whisper.load_model("large")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model: {e}")
            return

        try:
            self.status_label.config(text="Transcribing and translating...")
            self.update_idletasks()
            result = model.transcribe(input_file, task="translate", language=language)
        except Exception as e:
            messagebox.showerror("Error", f"Transcription failed: {e}")
            return

        # Remove duplicate segments
        filtered_segments = []
        prev_text = ""
        for segment in result["segments"]:
            current_text = segment["text"].strip()
            if current_text == prev_text:
                continue
            filtered_segments.append(segment)
            prev_text = current_text

        srt_file = self.save_file_dialog()
        if not srt_file:
            return

        try:
            with open(srt_file, "w", encoding="utf-8") as f:
                for i, segment in enumerate(filtered_segments, start=1):
                    start_time = self.format_time(segment["start"])
                    end_time = self.format_time(segment["end"])
                    text = segment["text"].strip()
                    f.write(f"{i}\n{start_time} --> {end_time}\n{text}\n\n")
            self.status_label.config(text=f"Subtitle saved to {srt_file}")
            messagebox.showinfo("Success", f"Subtitle saved to:\n{srt_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save SRT file: {e}")
    
    def start_transcription_wrapper(self):
        # Set the language_var to the code required by Whisper.
        lang_code = self.get_language_code()
        self.language_var.set(lang_code)
        self.start_transcription()

# =====================================================
# Tab 5: Video Downloader (from videodownloaderv7.py)
# =====================================================
class VideoDownloaderTab(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.create_widgets()
    
    def create_widgets(self):
        # URL Entry
        tk.Label(self, text="Video URL:").pack(pady=5)
        self.url_entry = tk.Entry(self, width=100)
        self.url_entry.pack(pady=5)

        # Output Directory selection
        output_frame = tk.Frame(self)
        output_frame.pack(pady=5)
        tk.Label(output_frame, text="Save to Folder:").pack(side='left', padx=5)
        self.output_dir = tk.StringVar()
        self.output_dir_entry = tk.Entry(output_frame, textvariable=self.output_dir, width=60)
        self.output_dir_entry.pack(side='left')
        tk.Button(output_frame, text="Browse", command=self.browse_output_dir).pack(side='left', padx=5)

        # yt-dlp Options
        options_frame = tk.Frame(self)
        options_frame.pack(pady=5, fill='x')
        tool_info = ("yt-dlp: Supports YouTube, Bilibili, Vimeo, Twitch, etc. "
                     "For videos requiring login, use a cookies.txt file.")
        tk.Label(options_frame, text=tool_info, wraplength=670, justify='left', fg="blue").pack(pady=5, padx=10)

        # Options variables
        self.audio_only = tk.BooleanVar()
        self.subtitles = tk.BooleanVar()
        self.embed_metadata = tk.BooleanVar()
        self.embed_thumbnail = tk.BooleanVar()
        self.no_check_certificate = tk.BooleanVar()
        self.cookies = tk.StringVar()
        self.format_choice = tk.StringVar(value="best")

        # Options checkbuttons and format selection
        tk.Checkbutton(options_frame, text="Audio Only (MP3)", variable=self.audio_only).pack(anchor='w', padx=10, pady=2)
        tk.Checkbutton(options_frame, text="Download Subtitles", variable=self.subtitles).pack(anchor='w', padx=10, pady=2)
        tk.Checkbutton(options_frame, text="Embed Metadata", variable=self.embed_metadata).pack(anchor='w', padx=10, pady=2)
        tk.Checkbutton(options_frame, text="Embed Thumbnail", variable=self.embed_thumbnail).pack(anchor='w', padx=10, pady=2)
        tk.Checkbutton(options_frame, text="Ignore SSL Certificate Errors", variable=self.no_check_certificate).pack(anchor='w', padx=10, pady=2)

        tk.Label(options_frame, text="Select Format / Resolution:").pack(anchor='w', padx=10)
        format_choices = [
            "best",
            "worst",
            "bestvideo+bestaudio",
            "worstvideo+worstaudio",
            "bv*+ba*",
            "bv[height<=720]+ba",
            "bv[height<=480]+ba",
            "bv[ext=mp4]+ba[ext=m4a]",
            "bv[height=720][fps<=30]+ba[abr<=128]"
        ]
        self.format_choice.set("best")
        tk.OptionMenu(options_frame, self.format_choice, *format_choices).pack(anchor='w', padx=10, pady=2)

        tk.Label(options_frame, text="Path to cookies.txt (for login):").pack(anchor='w', padx=10)
        cookies_frame = tk.Frame(options_frame)
        cookies_frame.pack(anchor='w', padx=10, pady=2)
        self.cookies_entry = tk.Entry(cookies_frame, textvariable=self.cookies, width=50)
        self.cookies_entry.pack(side='left')
        tk.Button(cookies_frame, text="Browse", command=self.browse_cookies).pack(side='left', padx=5)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100, mode='indeterminate')
        self.progress_bar.pack(fill='x', padx=10, pady=10)

        # Terminal output display
        output_frame2 = tk.Frame(self)
        output_frame2.pack(fill='both', expand=True, padx=10, pady=5)
        self.output_text = tk.Text(output_frame2, height=12, wrap='word')
        self.output_text.pack(side='left', fill='both', expand=True)
        scrollbar = ttk.Scrollbar(output_frame2, command=self.output_text.yview)
        scrollbar.pack(side='right', fill='y')
        self.output_text.configure(yscrollcommand=scrollbar.set)

        # Download button
        tk.Button(self, text="Download with yt-dlp", command=self.download_video).pack(pady=10)

    def browse_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)

    def browse_cookies(self):
        file = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if file:
            self.cookies.set(file)

    def run_command(self, tool, url, options):
        if not url:
            messagebox.showwarning("Input Error", "Please enter a URL")
            return

        self.progress_var.set(0)
        self.progress_bar.start()
        self.output_text.delete("1.0", tk.END)

        def thread_target():
            try:
                tool_path = shutil.which(tool)
                if not tool_path:
                    raise FileNotFoundError(f"The tool '{tool}' was not found in your system PATH.")

                cmd = [tool_path]

                output_path = options.get('output_dir')
                if output_path:
                    output_path = os.path.expanduser(output_path)
                    if not os.path.exists(output_path):
                        os.makedirs(output_path)

                if tool == 'yt-dlp':
                    if options.get('audio_only'):
                        cmd += ['-x', '--audio-format', 'mp3']
                    if options.get('subtitles'):
                        cmd += ['--write-sub']
                    if options.get('embed_metadata'):
                        cmd += ['--embed-metadata']
                    if options.get('embed_thumbnail'):
                        cmd += ['--embed-thumbnail']
                    if options.get('no_check_certificate'):
                        cmd += ['--no-check-certificate']
                    if options.get('format'):
                        cmd += ['-f', options['format']]
                    if options.get('cookies'):
                        cmd += ['--cookies', options['cookies']]
                    if output_path:
                        cmd += ['-P', output_path]

                cmd.append(url)

                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in process.stdout:
                    self.output_text.insert(tk.END, line)
                    self.output_text.see(tk.END)

                process.wait()
                self.progress_bar.stop()
                self.progress_var.set(100)
                messagebox.showinfo("Finished", f"Download with {tool} completed.")
            except Exception as e:
                self.progress_bar.stop()
                messagebox.showerror("Error", str(e))

        threading.Thread(target=thread_target).start()

    def download_video(self):
        url = self.url_entry.get()
        options = {
            'output_dir': self.output_dir.get(),
            'audio_only': self.audio_only.get(),
            'subtitles': self.subtitles.get(),
            'embed_metadata': self.embed_metadata.get(),
            'embed_thumbnail': self.embed_thumbnail.get(),
            'no_check_certificate': self.no_check_certificate.get(),
            'format': self.format_choice.get(),
            'cookies': self.cookies.get()
        }
        self.run_command('yt-dlp', url, options)

# =====================================================
# Main Application with Notebook (SuperApp)
# =====================================================
class SuperApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SuperApp")
        self.geometry("900x750")
        self.create_tabs()
    
    def create_tabs(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True)

        tab1 = MediaConverterTab(notebook)
        tab2 = OfflineTranslatorTab(notebook)
        tab3 = PDFTranslatorTab(notebook)
        tab4 = VideoTranslatorTab(notebook)
        tab5 = VideoDownloaderTab(notebook)

        notebook.add(tab1, text="Media Converter")
        notebook.add(tab2, text="Offline Translator")
        notebook.add(tab3, text="PDF Translator")
        notebook.add(tab4, text="Video Translator")
        notebook.add(tab5, text="Video Downloader")

if __name__ == "__main__":
    app = SuperApp()
    app.mainloop()

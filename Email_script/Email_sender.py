

import json
import os
import re
import smtplib
import ssl
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from email.message import EmailMessage

CREDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "credentials.json")

DEFAULT_SUBJECT = "Application for {role} — {your_name}"
DEFAULT_BODY = """Hi,

I hope you're doing well. I'm reaching out to express my interest in opportunities at your organization. Please find my resume attached for your review.

I'd welcome the chance to connect and discuss how I might contribute to your team.

Thank you for your time and consideration.

Best regards,
{your_name}
{your_phone}
{your_email}
"""

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ResumeEmailerApp:
    def __init__(self, root):
        self.root = root
        root.title("Bulk Resume Emailer")
        root.geometry("700x750")

        pad = {"padx": 10, "pady": 5}

        # --- Gmail credentials ---
        frame_creds = ttk.LabelFrame(root, text="Your Gmail (sender)")
        frame_creds.pack(fill="x", **pad)

        ttk.Label(frame_creds, text="Gmail address:").grid(row=0, column=0, sticky="w")
        self.sender_email = ttk.Entry(frame_creds, width=40)
        self.sender_email.grid(row=0, column=1, sticky="w", padx=5, pady=3)

        ttk.Label(frame_creds, text="App password (16 chars):").grid(row=1, column=0, sticky="w")
        self.app_password = ttk.Entry(frame_creds, width=40, show="*")
        self.app_password.grid(row=1, column=1, sticky="w", padx=5, pady=3)

        self.remember_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame_creds,
            text="Remember me on this computer (saves to credentials.json in plain text)",
            variable=self.remember_var,
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=3)

        self.load_saved_credentials()

        # --- Your details (used in template placeholders) ---
        frame_you = ttk.LabelFrame(root, text="Your details (used in email template)")
        frame_you.pack(fill="x", **pad)

        ttk.Label(frame_you, text="Your name:").grid(row=0, column=0, sticky="w")
        self.your_name = ttk.Entry(frame_you, width=30)
        self.your_name.grid(row=0, column=1, sticky="w", padx=5, pady=3)

        ttk.Label(frame_you, text="Your phone:").grid(row=1, column=0, sticky="w")
        self.your_phone = ttk.Entry(frame_you, width=30)
        self.your_phone.grid(row=1, column=1, sticky="w", padx=5, pady=3)

        ttk.Label(frame_you, text="Role you're applying for:").grid(row=2, column=0, sticky="w")
        self.role = ttk.Entry(frame_you, width=30)
        self.role.grid(row=2, column=1, sticky="w", padx=5, pady=3)
        self.role.insert(0, "Software Developer")

        # --- Recipients ---
        frame_recipients = ttk.LabelFrame(root, text="Recipient emails (one per line, or comma-separated)")
        frame_recipients.pack(fill="both", expand=False, **pad)
        self.recipients_box = scrolledtext.ScrolledText(frame_recipients, height=6)
        self.recipients_box.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Resume attachment ---
        frame_resume = ttk.LabelFrame(root, text="Resume attachment")
        frame_resume.pack(fill="x", **pad)
        self.resume_path_var = tk.StringVar(value="No file selected")
        ttk.Label(frame_resume, textvariable=self.resume_path_var).pack(side="left", padx=5)
        ttk.Button(frame_resume, text="Choose File...", command=self.choose_resume).pack(side="right", padx=5)

        # --- Subject ---
        frame_subject = ttk.LabelFrame(root, text="Subject (placeholders: {role} {your_name})")
        frame_subject.pack(fill="x", **pad)
        self.subject_entry = ttk.Entry(frame_subject)
        self.subject_entry.pack(fill="x", padx=5, pady=5)
        self.subject_entry.insert(0, DEFAULT_SUBJECT)

        # --- Body ---
        frame_body = ttk.LabelFrame(
            root, text="Email body (placeholders: {your_name} {your_phone} {your_email} {role})"
        )
        frame_body.pack(fill="both", expand=True, **pad)
        self.body_box = scrolledtext.ScrolledText(frame_body, height=10)
        self.body_box.pack(fill="both", expand=True, padx=5, pady=5)
        self.body_box.insert("1.0", DEFAULT_BODY)

        # --- Send button + progress ---
        frame_send = ttk.Frame(root)
        frame_send.pack(fill="x", **pad)
        self.send_btn = ttk.Button(frame_send, text="Send Emails", command=self.start_send_thread)
        self.send_btn.pack(side="left", padx=5)
        self.progress_var = tk.StringVar(value="")
        ttk.Label(frame_send, textvariable=self.progress_var).pack(side="left", padx=10)

        self.log_box = scrolledtext.ScrolledText(root, height=8, state="disabled")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=5)

    def load_saved_credentials(self):
        if os.path.isfile(CREDS_FILE):
            try:
                with open(CREDS_FILE, "r") as f:
                    data = json.load(f)
                self.sender_email.insert(0, data.get("email", ""))
                self.app_password.insert(0, data.get("app_password", ""))
                self.remember_var.set(True)
            except Exception:
                pass  # ignore a corrupt/unreadable creds file, just start blank

    def save_credentials(self, email, password):
        try:
            with open(CREDS_FILE, "w") as f:
                json.dump({"email": email, "app_password": password}, f)
        except Exception as e:
            self.log(f"⚠ Could not save credentials: {e}")

    def clear_saved_credentials(self):
        if os.path.isfile(CREDS_FILE):
            try:
                os.remove(CREDS_FILE)
            except Exception:
                pass

    def choose_resume(self):
        path = filedialog.askopenfilename(
            title="Select your resume",
            filetypes=[("Documents", "*.pdf *.docx *.doc"), ("All files", "*.*")],
        )
        if path:
            self.resume_path_var.set(path)

    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def parse_recipients(self):
        raw = self.recipients_box.get("1.0", "end")
        # split on newlines and commas
        parts = re.split(r"[,\n]", raw)
        emails = [p.strip() for p in parts if p.strip()]
        valid, invalid = [], []
        for e in emails:
            (valid if EMAIL_REGEX.match(e) else invalid).append(e)
        return valid, invalid

    def start_send_thread(self):
        sender = self.sender_email.get().strip()
        password = self.app_password.get().strip()
        resume_path = self.resume_path_var.get()

        if not sender or not EMAIL_REGEX.match(sender):
            messagebox.showerror("Error", "Enter a valid Gmail address.")
            return
        if not password:
            messagebox.showerror("Error", "Enter your Gmail App Password.")
            return
        if resume_path == "No file selected" or not os.path.isfile(resume_path):
            messagebox.showerror("Error", "Choose a valid resume file.")
            return

        valid, invalid = self.parse_recipients()
        if not valid:
            messagebox.showerror("Error", "No valid recipient emails found.")
            return
        if invalid:
            if not messagebox.askyesno(
                "Some emails look invalid",
                f"These will be skipped:\n{', '.join(invalid)}\n\nContinue with the {len(valid)} valid ones?",
            ):
                return

        if not messagebox.askyesno(
            "Confirm",
            f"Send email + resume to {len(valid)} recipient(s) from {sender}?",
        ):
            return

        if self.remember_var.get():
            self.save_credentials(sender, password)
        else:
            self.clear_saved_credentials()

        self.send_btn.configure(state="disabled")
        thread = threading.Thread(
            target=self.send_all, args=(sender, password, resume_path, valid), daemon=True
        )
        thread.start()

    def send_all(self, sender, password, resume_path, recipients):
        subject_template = self.subject_entry.get()
        body_template = self.body_box.get("1.0", "end")

        context = ssl.create_default_context()
        sent, failed = 0, []

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(sender, password)

                for i, recipient in enumerate(recipients, start=1):
                    self.progress_var.set(f"Sending {i}/{len(recipients)}...")
                    try:
                        msg = EmailMessage()
                        subject = subject_template.format(
                            role=self.role.get(), your_name=self.your_name.get()
                        )
                        body = body_template.format(
                            your_name=self.your_name.get(),
                            your_phone=self.your_phone.get(),
                            your_email=sender,
                            role=self.role.get(),
                        )
                        msg["Subject"] = subject
                        msg["From"] = sender
                        msg["To"] = recipient
                        msg.set_content(body)

                        with open(resume_path, "rb") as f:
                            data = f.read()
                        filename = os.path.basename(resume_path)
                        maintype = "application"
                        subtype = "octet-stream"
                        if filename.lower().endswith(".pdf"):
                            subtype = "pdf"
                        elif filename.lower().endswith(".docx"):
                            subtype = "vnd.openxmlformats-officedocument.wordprocessingml.document"
                        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

                        server.send_message(msg)
                        sent += 1
                        self.log(f"✔ Sent to {recipient}")
                    except Exception as e:
                        failed.append((recipient, str(e)))
                        self.log(f"✘ Failed to {recipient}: {e}")

                    time.sleep(2)  # small delay between sends, be gentle on the SMTP server

        except smtplib.SMTPAuthenticationError:
            self.log("✘ Login failed. Check your Gmail address and App Password.")
            messagebox.showerror(
                "Authentication failed",
                "Gmail rejected the login. Make sure you're using an App Password "
                "(not your normal password) and that 2-Step Verification is enabled.",
            )
        except Exception as e:
            self.log(f"✘ Connection error: {e}")
            messagebox.showerror("Error", str(e))
        finally:
            self.progress_var.set(f"Done: {sent} sent, {len(failed)} failed.")
            self.send_btn.configure(state="normal")
            summary = f"Sent: {sent}\nFailed: {len(failed)}"
            if failed:
                summary += "\n\n" + "\n".join(f"{r}: {err}" for r, err in failed)
            messagebox.showinfo("Finished", summary)


if __name__ == "__main__":
    root = tk.Tk()
    app = ResumeEmailerApp(root)
    root.mainloop()

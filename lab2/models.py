"""
Pydantic Models for PDF Exfiltration Data Collection
Educational security research data structures
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class RequestMethod(str, Enum):
    """HTTP request method types"""
    GET = "GET"
    POST = "POST"
    POST_FORM = "POST (Form)"


class PDFReaderData(BaseModel):
    """Data collected from PDF reader environment"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "reader": "Reader",
                "viewer_version": "23.001.20093",
                "platform": "WIN",
                "language": "ENU"
            }
        }
    )

    reader: Optional[str] = Field(None, description="PDF Reader type (e.g., 'Reader', 'Exchange')")
    viewer_version: Optional[str] = Field(None, description="PDF viewer version string")
    app_version: Optional[str] = Field(None, description="Application version")
    platform: Optional[str] = Field(None, description="Operating system platform (WIN, Mac, UNIX)")
    language: Optional[str] = Field(None, description="System language code (e.g., 'ENU', 'ESP')")


class DocumentData(BaseModel):
    """Data about the PDF document itself"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "doc_title": "Security Report 2024",
                "doc_author": "Security Team",
                "doc_filename": "malicious_document.pdf",
                "doc_path": "C:/Users/student/Downloads/malicious_document.pdf",
                "num_pages": "1"
            }
        }
    )

    doc_title: Optional[str] = Field(None, description="Document title")
    doc_author: Optional[str] = Field(None, description="Document author")
    doc_subject: Optional[str] = Field(None, description="Document subject")
    doc_creator: Optional[str] = Field(None, description="Document creator application")
    doc_producer: Optional[str] = Field(None, description="PDF producer")
    doc_filename: Optional[str] = Field(None, description="Filename of the document")
    doc_path: Optional[str] = Field(None, description="Full file path (if accessible)")
    num_pages: Optional[str] = Field(None, description="Number of pages in document")


class SystemData(BaseModel):
    """System and environment data"""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "username": "john.doe",
                "screen_width": "1920",
                "screen_height": "1080",
                "timezone_offset": "-300"
            }
        }
    )

    username: Optional[str] = Field(None, description="Username or login name")
    email: Optional[str] = Field(None, description="User email if available")
    screen_width: Optional[str] = Field(None, description="Screen width in pixels")
    screen_height: Optional[str] = Field(None, description="Screen height in pixels")
    screen_depth: Optional[str] = Field(None, description="Screen color depth")
    timezone_offset: Optional[str] = Field(None, description="Timezone offset in minutes")
    timestamp: Optional[str] = Field(None, description="Client-side timestamp")


class ExfiltratedData(BaseModel):
    """Complete exfiltrated data from PDF"""
    model_config = ConfigDict(extra='allow')  # Allow additional fields

    # Reader data
    reader: Optional[str] = None
    viewer_version: Optional[str] = None
    app_version: Optional[str] = None
    platform: Optional[str] = None
    language: Optional[str] = None

    # Document data
    doc_title: Optional[str] = None
    doc_author: Optional[str] = None
    doc_subject: Optional[str] = None
    doc_creator: Optional[str] = None
    doc_producer: Optional[str] = None
    doc_filename: Optional[str] = None
    doc_path: Optional[str] = None
    num_pages: Optional[str] = None

    # System data
    username: Optional[str] = None
    email: Optional[str] = None
    screen_width: Optional[str] = None
    screen_height: Optional[str] = None
    screen_depth: Optional[str] = None
    timezone_offset: Optional[str] = None
    timestamp: Optional[str] = None

    # Additional custom fields allowed via ConfigDict(extra='allow')

    def to_categorized(self) -> Dict[str, Any]:
        """Return data organized by category"""
        return {
            "reader_info": PDFReaderData(
                reader=self.reader,
                viewer_version=self.viewer_version,
                app_version=self.app_version,
                platform=self.platform,
                language=self.language
            ).model_dump(exclude_none=True),
            "document_info": DocumentData(
                doc_title=self.doc_title,
                doc_author=self.doc_author,
                doc_subject=self.doc_subject,
                doc_creator=self.doc_creator,
                doc_producer=self.doc_producer,
                doc_filename=self.doc_filename,
                doc_path=self.doc_path,
                num_pages=self.num_pages
            ).model_dump(exclude_none=True),
            "system_info": SystemData(
                username=self.username,
                email=self.email,
                screen_width=self.screen_width,
                screen_height=self.screen_height,
                screen_depth=self.screen_depth,
                timezone_offset=self.timezone_offset,
                timestamp=self.timestamp
            ).model_dump(exclude_none=True)
        }


class CollectionEntry(BaseModel):
    """Single data collection entry with metadata"""
    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()},
        json_schema_extra={
            "example": {
                "timestamp": "2024-12-03T14:23:45.123456",
                "method": "GET",
                "client_ip": "192.168.1.50",
                "user_agent": "Mozilla/5.0...",
                "collected_data": {
                    "reader": "Reader",
                    "viewer_version": "23.001.20093",
                    "platform": "WIN",
                    "language": "ENU",
                    "doc_filename": "malicious_document.pdf"
                },
                "headers": {
                    "host": "localhost:8000",
                    "user-agent": "Mozilla/5.0..."
                }
            }
        }
    )

    timestamp: datetime = Field(default_factory=datetime.now, description="Server timestamp of collection")
    method: RequestMethod = Field(..., description="HTTP method used for exfiltration")
    client_ip: str = Field(..., description="Client IP address")
    user_agent: str = Field(default="unknown", description="User-Agent header")
    collected_data: ExfiltratedData = Field(..., description="Exfiltrated data from PDF")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")


class PostCollectionEntry(BaseModel):
    """Collection entry for POST requests with body data"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    timestamp: datetime = Field(default_factory=datetime.now, description="Server timestamp")
    method: RequestMethod = Field(..., description="HTTP method used")
    client_ip: str = Field(..., description="Client IP address")
    user_agent: str = Field(default="unknown", description="User-Agent header")
    body: Dict[str, Any] | str = Field(..., description="Request body (JSON or raw)")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")


class FormCollectionEntry(BaseModel):
    """Collection entry for form submissions"""
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})

    timestamp: datetime = Field(default_factory=datetime.now, description="Server timestamp")
    method: RequestMethod = Field(default=RequestMethod.POST_FORM, description="HTTP method")
    client_ip: str = Field(..., description="Client IP address")
    form_data: Dict[str, Any] | str = Field(..., description="Form data submitted")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")


class DataResponse(BaseModel):
    """Response model for viewing collected data"""
    total_entries: int = Field(..., description="Total number of collected entries")
    data: List[Dict[str, Any]] = Field(..., description="List of all collected entries")


class StatsResponse(BaseModel):
    """Response model for statistics"""
    total_entries: int = Field(..., description="Total number of entries")
    by_method: Dict[str, int] = Field(..., description="Count by HTTP method")
    by_ip: Dict[str, int] = Field(..., description="Count by client IP")
    first_seen: Optional[str] = Field(None, description="Timestamp of first entry")
    last_seen: Optional[str] = Field(None, description="Timestamp of last entry")


class ClearDataResponse(BaseModel):
    """Response model for clearing data"""
    status: str = Field(..., description="Operation status")
    entries_cleared: int = Field(..., description="Number of entries cleared")


class SuccessResponse(BaseModel):
    """Generic success response"""
    status: str = Field(default="success", description="Operation status")
    message: Optional[str] = Field(None, description="Optional message")


class ServiceInfo(BaseModel):
    """Root endpoint service information"""
    service: str = Field(default="PDF Exfiltration Collector", description="Service name")
    status: str = Field(default="running", description="Service status")
    purpose: str = Field(default="Educational security research", description="Purpose")
    endpoints: Dict[str, str] = Field(..., description="Available endpoints")
    version: str = Field(default="2.0.0", description="API version")


# Risk assessment models
class RiskLevel(str, Enum):
    """Risk assessment levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ThreatIndicators(BaseModel):
    """Threat indicators found in collected data"""
    suspicious_paths: List[str] = Field(default_factory=list, description="Suspicious file paths")
    exposed_usernames: List[str] = Field(default_factory=list, description="Exposed usernames")
    system_platforms: List[str] = Field(default_factory=list, description="Identified platforms")
    vulnerable_readers: List[str] = Field(default_factory=list, description="Vulnerable reader versions")


class RiskAssessment(BaseModel):
    """Risk assessment for collected data"""
    risk_level: RiskLevel = Field(..., description="Overall risk level")
    score: int = Field(..., ge=0, le=100, description="Risk score (0-100)")
    indicators: ThreatIndicators = Field(..., description="Threat indicators")
    recommendations: List[str] = Field(default_factory=list, description="Security recommendations")

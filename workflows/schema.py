"""
Workflow Schema
===============
Pydantic models defining the structure for captured banking workflows.
Each workflow represents a user journey (e.g., "Apply for a credit card").
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ElementType(str, Enum):
    BUTTON = "button"
    LINK = "link"
    INPUT = "input"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    FORM = "form"
    TABLE = "table"
    CARD = "card"
    MODAL = "modal"
    ACCORDION = "accordion"
    TAB = "tab"
    NAVIGATION = "navigation"
    HERO = "hero"
    CALLOUT = "callout"


class InteractiveElement(BaseModel):
    """A UI element the user can interact with."""
    element_type: ElementType
    selector: str = Field(description="CSS selector for the element")
    label: str = Field(description="Visible text or aria-label")
    action: str = Field(description="What happens when interacted with")
    target_url: Optional[str] = None
    required: bool = False
    placeholder: Optional[str] = None
    options: list[str] = Field(default_factory=list, description="For select/radio elements")


class FormField(BaseModel):
    """A field within a form."""
    name: str
    label: str
    field_type: str  # text, email, tel, number, select, checkbox, etc.
    required: bool = False
    placeholder: Optional[str] = None
    validation_rules: Optional[str] = None
    options: list[str] = Field(default_factory=list)


class PageSection(BaseModel):
    """A distinct section of a page."""
    section_id: str
    title: str
    content_summary: str
    elements: list[InteractiveElement] = Field(default_factory=list)
    forms: list[FormField] = Field(default_factory=list)


class NavigationItem(BaseModel):
    """A navigation menu item."""
    label: str
    url: str
    children: list[NavigationItem] = Field(default_factory=list)


class PageCapture(BaseModel):
    """A single captured page in a workflow."""
    url: str
    title: str
    category: str
    meta_description: Optional[str] = None
    breadcrumbs: list[str] = Field(default_factory=list)
    sections: list[PageSection] = Field(default_factory=list)
    navigation: list[NavigationItem] = Field(default_factory=list)
    screenshot_path: Optional[str] = None
    raw_html_path: Optional[str] = None
    captured_at: datetime = Field(default_factory=datetime.now)


class WorkflowStep(BaseModel):
    """A single step in a user workflow."""
    step_number: int
    page: PageCapture
    user_action: str = Field(description="What the user does on this page")
    expected_outcome: str = Field(description="What happens after the action")
    next_step_trigger: Optional[str] = Field(
        None, description="What triggers moving to the next step"
    )


class Workflow(BaseModel):
    """A complete user workflow / journey."""
    workflow_id: str
    name: str
    category: str
    description: str
    steps: list[WorkflowStep] = Field(default_factory=list)
    entry_point: str = Field(description="URL where this workflow starts")
    estimated_completion_time: Optional[str] = None
    prerequisites: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class WorkflowCollection(BaseModel):
    """Collection of all captured workflows."""
    source: str = "TD Canada Trust - Personal Banking"
    base_url: str = "https://www.td.com/ca/en/personal-banking"
    workflows: list[Workflow] = Field(default_factory=list)
    total_pages_captured: int = 0
    capture_date: datetime = Field(default_factory=datetime.now)

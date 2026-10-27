# models/test_results.py

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from enum import Enum, IntEnum
import re


# Enums

class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"

class ActionType(str, Enum):
    CLICK = "click"
    TAP = "tap"
    TYPE = "type"
    INPUT = "input"
    SCROLL = "scroll"
    SWIPE = "swipe"
    WAIT = "wait"
    SLEEP = "sleep"
    OPEN_APP = "open_app"
    LAUNCH = "launch"
    ASSERT = "assert"
    VERIFY = "verify"
    BACK = "back"
    NAVIGATE = "navigate"
    LONG_PRESS = "long_press"
    HOME = "home"
    UNKNOWN = "unknown"

class Verbosity(IntEnum):
    SILENT = 0
    SUMMARY = 1
    COMPACT = 2
    DETAILED = 3

class Droidrun_Output(IntEnum):
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


# Alias Maps

ACTION_TYPE_ALIASES = {
    "press": "click",
    "pressed": "click",
    "clicked": "click",
    "tapped": "tap",
    "touch": "tap",
    "enter": "type",
    "fill": "type",
    "text": "type",
    "type_text": "type",
    "scroll_down": "scroll",
    "scroll_up": "scroll",
    "swipe_left": "swipe",
    "swipe_right": "swipe",
    "swipe_up": "swipe",
    "swipe_down": "swipe",
    "open": "open_app",
    "start": "launch",
    "check": "assert",
    "validate": "verify",
    "confirm": "verify",
    "go_back": "back",
    "press_back": "back",
    "go_home": "home",
    "press_home": "home",
    "hold": "long_press",
    "long_click": "long_press",
}

STATUS_ALIASES = {
    "pass": "passed",
    "fail": "failed",
    "failure": "failed",
    "err": "error",
    "crash": "error",
    "success": "passed",
}


# ActionRecord

class ActionRecord(BaseModel):
    step_number: int = Field(
        ...,
        ge=1,
        description="Sequential step number starting from 1."
    )
    action_type: ActionType = Field(
        ...,
        description="The type of UI action performed."
    )
    target_element: Optional[str] = Field(
        default=None,
        description=(
            "The UI element targeted. Use descriptive names "
            "like 'Play button', 'Search input field'. "
            "Null only for actions with no target such as wait, sleep, or back."
        ),
    )
    success: bool = Field(
        ...,
        description=(
            "True if this specific action completed successfully. "
            "False if the element was not found or the action failed."
        ),
    )
    reasoning: str = Field(
        ...,
        min_length=10,
        max_length=200,
        description=(
            "One sentence: why this action was taken and what happened. "
            "Example: 'Tapped Play button to start live stream, video began loading.'"
        ),
    )

    @field_validator('action_type', mode='before')
    @classmethod
    def normalize_action_type(cls, v):
        if isinstance(v, str):
            cleaned = v.lower().strip().replace(" ", "_")
            return ACTION_TYPE_ALIASES.get(cleaned, cleaned)
        return v

    @field_validator('step_number', mode='before')
    @classmethod
    def fix_zero_indexed_steps(cls, v):
        if isinstance(v, int) and v == 0:
            return 1
        return v

    @field_validator('target_element', mode='after')
    @classmethod
    def clean_target_element(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if cleaned.lower() in ('n/a', 'none', 'null', 'na', '-', ''):
            return None
        return cleaned


# Expected Criteria

class ElementCheck(BaseModel):
    element: str = Field(
        description="What to look for on screen."
    )
    check_type: str = Field(
        default="text",
        description="How to verify: 'text', 'structural', or 'visual'."
    )
    aliases: List[str] = Field(
        default_factory=list,
        description="Alternative names the LLM might use for this element."
    )
    critical: bool = Field(
        default=True,
        description="If True, missing this element fails the test. If False, it's a warning."
    )


class ExpectedCriteria(BaseModel):
    required_elements: List[ElementCheck] = Field(
        default_factory=list,
        description=(
            "Elements that MUST be present on the final screen. "
            "Confirm each one explicitly in your observations."
        ),
    )
    forbidden_elements: List[ElementCheck] = Field(
        default_factory=list,
        description=(
            "Elements that must NOT be present. "
            "If any of these are present, the test has failed."
        ),
    )
    required_state: Optional[str] = Field(
        default=None,
        description="Expected final app state description.",
    )


# TestCaseResult

class TestCaseResult(BaseModel):
    test_id: str = Field(
        ...,
        description="The test case ID exactly as provided."
    )
    test_name: str = Field(
        ...,
        description="The test name exactly as provided."
    )
    status: TestStatus = Field(
        ...,
        description=(
            "'passed' if the test completed and assertion succeeded. "
            "'failed' if the test completed but assertion did not succeed. "
            "'error' if the test could not complete."
        ),
    )
    actions_taken: List[ActionRecord] = Field(
        default_factory=list,
        description="Ordered list of every UI action performed during the test."
    )
    total_steps: int = Field(
        default=0,
        ge=0,
        description="Total number of actions. Must match length of actions_taken."
    )
    assertion_passed: bool = Field(
        ...,
        description=(
            "Must be True when status is 'passed'. "
            "Must be False when status is 'failed' or 'error'."
        ),
    )
    failure_reason: Optional[str] = Field(
        default=None,
        description=(
            "ONLY populate when status is 'failed' or 'error'. "
            "Must be null when status is 'passed'."
        ),
    )
    observations: str = Field(
        ...,
        min_length=20,
        description=(
            "Describe the final screen state in 1-3 sentences. "
            "Must include: "
            "1) What screen is displayed, "
            "2) Key UI elements visible or missing, "
            "3) Whether expected outcome was confirmed. "
            "Do NOT write a full test report. Do NOT repeat the steps taken. "
            "Just describe what you see on the final screen."
        ),
    )
    expected_criteria: Optional[ExpectedCriteria] = Field(
        default=None,
        description=(
            "The pass/fail criteria for this test. "
            "Your observations MUST address every element listed here."
        ),
    )

    # Field Validators

    @field_validator('status', mode='before')
    @classmethod
    def normalize_status(cls, v):
        if isinstance(v, str):
            cleaned = v.lower().strip()
            return STATUS_ALIASES.get(cleaned, cleaned)
        return v

    @field_validator('failure_reason', mode='after')
    @classmethod
    def clean_failure_reason(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if cleaned.lower() in ('n/a', 'none', 'null', 'na', '-', ''):
            return None
        return cleaned

    # Model Validator

    @model_validator(mode='after')
    def enforce_consistency(self):
        # Auto-calculate total_steps
        if self.actions_taken:
            self.total_steps = len(self.actions_taken)

        # Fix step numbering
        for i, action in enumerate(self.actions_taken):
            if action.step_number != i + 1:
                action.step_number = i + 1

        # Validate against expected criteria
        if self.expected_criteria:
            criteria_issues = self._check_criteria()
            if criteria_issues and self.status == TestStatus.PASSED:
                self.status = TestStatus.FAILED
                self.assertion_passed = False
                self.failure_reason = (
                    f"LLM reported PASSED but criteria validation failed: "
                    f"{'; '.join(criteria_issues)}"
                )

        # PASSED: force consistent state
        if self.status == TestStatus.PASSED:
            self.assertion_passed = True
            if self.failure_reason:
                if self.failure_reason not in self.observations:
                    self.observations = (
                        f"{self.observations} "
                        f"[Agent note: {self.failure_reason}]"
                    )
                self.failure_reason = None

        # FAILED: force consistent state
        if self.status == TestStatus.FAILED:
            self.assertion_passed = False
            if not self.failure_reason:
                self.failure_reason = "Test failed but no failure reason was provided."

        # ERROR: force consistent state
        if self.status == TestStatus.ERROR:
            self.assertion_passed = False
            if not self.failure_reason:
                self.failure_reason = "Test errored but no error details were provided."

        return self

    # Criteria Checking

    def _check_criteria(self) -> List[str]:
        issues = []
        warnings = []
        obs_lower = self.observations.lower()
        for check in self.expected_criteria.required_elements:
            found = self._element_mentioned(check, obs_lower)
            if not found:
                msg = f"Required element '{check.element}' not confirmed in observations"
                if check.critical:
                    issues.append(msg)
                else:
                    warnings.append(msg)
        for check in self.expected_criteria.forbidden_elements:
            if self._element_present(check, obs_lower):
                msg = f"Forbidden element '{check.element}' appears to be present"
                if check.critical:
                    issues.append(msg)
                else:
                    warnings.append(msg)
        if warnings:
            self.observations += f" [Criteria warnings: {'; '.join(warnings)}]"
        return issues

    def _element_mentioned(self, check: ElementCheck, obs_lower: str) -> bool:
        primary = check.element.lower()

        core_words = [primary]
        for suffix in [' tab', ' button', ' icon', ' field', ' screen', ' dialog', ' bar']:
            if primary.endswith(suffix):
                core_words.append(primary.replace(suffix, '').strip())
                break

        # Sentence-level negative indicators
        negative_indicators = [
            "missing", "is missing", "are missing",             
            "not visible", "not present", "not shown",
            "not displayed", "absent", "did not see", "could not find",
            "were not", "was not", "not found", "not appear",
            "not loaded", "not available", "not contain",        
            "lacks", "lacking", "without",                       
            "doesn't have", "does not have",                     
        ]

        # Split into sentences
        clauses = re.split(r'[.;!\n]+', obs_lower)
        clauses = [c.strip() for c in clauses if c.strip()]

        for word in core_words:
            for clause in clauses:
                if word in clause:
                    # Check if this sentence is negative
                    is_negative = any(neg in clause for neg in negative_indicators)
                    if not is_negative:
                        return True

        for alias in check.aliases:
            alias_lower = alias.lower()
            for clause in clauses:
                if alias_lower in clause:
                    is_negative = any(neg in clause for neg in negative_indicators)
                    if not is_negative:
                        return True

        return False

    def _element_present(self, check: ElementCheck, obs_lower: str) -> bool:
        names = [check.element.lower()] + [a.lower() for a in check.aliases]
        present_patterns = [
            "{name} is visible",
            "{name} is displayed",
            "{name} is shown",
            "{name} appeared",
            "{name} is present",
            "see {name}",
            "seeing {name}",
            "showing {name}",
            "shows {name}",
            "found {name}",
            "{name} was found",
            "{name} popped up",
        ]
        for name in names:
            for pattern in present_patterns:
                if pattern.format(name=name) in obs_lower:
                    return True
        return False

    # Display Helpers

    def step_count(self) -> int:
        if self.actions_taken:
            return len(self.actions_taken)
        return self.total_steps

    def _status_icon(self) -> str:
        return "✅" if self.status == TestStatus.PASSED else "❌"

    def _status_text(self) -> str:
        if self.status == TestStatus.PASSED:
            return "[green][PASSED][/green]"
        elif self.status == TestStatus.FAILED:
            return "[red][FAILED][/red]"
        else:
            return "[red][ERROR][/red]"

    def _assertion_text(self) -> str:
        if self.assertion_passed:
            return "[green]PASSED ✅[/green]"
        return "[red]FAILED ❌[/red]"

    def _action_color(self, action_type) -> str:
        colors = {
            ActionType.CLICK: "cyan",
            ActionType.TAP: "cyan",
            ActionType.TYPE: "yellow",
            ActionType.INPUT: "yellow",
            ActionType.WAIT: "dim",
            ActionType.SLEEP: "dim",
            ActionType.SCROLL: "magenta",
            ActionType.SWIPE: "magenta",
            ActionType.OPEN_APP: "green",
            ActionType.LAUNCH: "green",
            ActionType.ASSERT: "blue",
            ActionType.VERIFY: "blue",
            ActionType.BACK: "red",
            ActionType.NAVIGATE: "bright_blue",
            ActionType.LONG_PRESS: "cyan",
            ActionType.HOME: "green",
            ActionType.UNKNOWN: "white",
        }
        return colors.get(action_type, "white")

    def display(self, verbosity: Verbosity = Verbosity.SUMMARY) -> str:
        if verbosity == Verbosity.SILENT:
            return ""
        if verbosity == Verbosity.SUMMARY:
            return self._summary()
        if verbosity == Verbosity.COMPACT:
            return self._compact()
        return self._detailed()

    def _summary(self) -> str:
        line = (
            f"{self._status_icon()} {self.test_id} — {self.test_name} "
            f"{self._status_text()} ({self.step_count()} steps)"
        )
        if self.failure_reason:
            line += f"\n   ↳ [red]{self.failure_reason}[/red]"
        return line

    def _compact(self) -> str:
        lines = [self._summary()]
        if self.status == TestStatus.PASSED and self.observations:
            lines.append(f"   [dim]Observations: {self.observations}[/dim]")
        failed = [a for a in self.actions_taken if not a.success]
        if failed:
            lines.append("")
            lines.append("  [red]Failed steps:[/red]")
            for action in failed:
                target = action.target_element or "N/A"
                lines.append(
                    f"    Step {action.step_number}  ❌  "
                    f"{action.action_type.value:<14}"
                    f"→ {target:<24}"
                    f'[red]"{action.reasoning}"[/red]'
                )
        return "\n".join(lines)

    def _detailed(self) -> str:
        lines = [
            f"{'='*70}",
            f"  {self._status_icon()}  {self.test_id} — {self.test_name} {self._status_text()}",
            f"{'='*70}",
            "",
        ]
        for action in self.actions_taken:
            target = action.target_element or "N/A"
            color = self._action_color(action.action_type)
            if action.success:
                step_icon = "✅"
                reasoning = f'"{action.reasoning}"'
            else:
                step_icon = "❌"
                reasoning = f'[red]"{action.reasoning}"[/red]'
            lines.append(
                f"  Step {action.step_number:<3} {step_icon}  "
                f"[{color}]{action.action_type.value:<14}[/{color}]"
                f"→ {target:<24}"
                f"{reasoning}"
            )
        lines.append("")
        lines.append(f"  Total Steps:  {self.step_count()}")
        lines.append(f"  Assertion:    {self._assertion_text()}")
        if self.failure_reason:
            lines.append(f"  Failure:      [red]{self.failure_reason}[/red]")
        if self.observations:
            lines.append(f"  Observations: {self.observations}")
        if self.expected_criteria:
            lines.append("")
            lines.append(f"  Criteria Validation:")
            for check in self.expected_criteria.required_elements:
                found = self._element_mentioned(check, self.observations.lower())
                icon = "✅" if found else ("❌" if check.critical else "⚠️")
                lines.append(f"    {icon} Required: {check.element}")
            for check in self.expected_criteria.forbidden_elements:
                present = self._element_present(check, self.observations.lower())
                icon = "❌" if present else "✅"
                lines.append(f"    {icon} Forbidden: {check.element}")
        return "\n".join(lines)
"""ADAM Sovereignty Connector.

A local orchestrator + AI-passthrough that installs and deploys the ADAM
(Autonomy Doctrine & Architecture Model) reference stack on a single Windows 11
host, fully isolated from public cloud.

The connector exposes two control-plane surfaces:
  * an HTTP API (for operators / dashboards)
  * a Model Context Protocol (MCP) server (for Claude and other LLMs)

All privileged actions pass through a vetted command catalog with audit
logging so the AI can drive the install safely.
"""

__version__ = "1.1.0"
__author__ = "Michael - ADAM Project"
__license__ = "Apache-2.0"

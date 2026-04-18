# Skill-Provided CodeAgent Tools — 100 Real-World Ideas

> Skills can extend the CodeAgent by shipping a `tools/` directory with Python modules.
> Each module exports a `TOOLS` dict mapping function names to callables, which are
> automatically injected into the CodeAgent's execution namespace.
>
> This document lists 100 real-world skill tool ideas across categories.

---

## 📝 Note-Taking & Knowledge Management

### 1. Obsidian Local API ✅ (implemented)
```
obsidian_search, obsidian_read, obsidian_write, obsidian_append, obsidian_list, obsidian_delete
```
Manage Obsidian vault notes, search, and metadata via the Local REST API plugin.

### 2. Notion API
```
notion_query_db, notion_create_page, notion_update_page, notion_search, notion_append_block
```
Full Notion workspace integration — query databases, create and update pages, append content blocks.

### 3. Logseq
```
logseq_search, logseq_get_page, logseq_create_page, logseq_append_block, logseq_get_graph_info
```
Interact with Logseq knowledge graphs via its HTTP API.

### 4. Roam Research
```
roam_query, roam_create_block, roam_update_block, roam_search, roam_daily_note
```
Block-level access to Roam graphs.

### 5. Joplin
```
joplin_search, joplin_get_note, joplin_create_note, joplin_update_note, joplin_list_notebooks
```
Manage Joplin notes and notebooks.

---

## 📊 Data Science & Analytics

### 6. DuckDB Analytics ✅ (implemented)
```
duckdb_query, duckdb_sql, duckdb_load_csv, duckdb_load_parquet, duckdb_load_json, duckdb_tables, duckdb_describe, duckdb_export_csv
```
In-process SQL analytics on CSV, Parquet, and JSON files — no server required.

### 7. Pandas DataFrame Operations
```
df_from_csv, df_from_json, df_describe, df_query, df_to_csv, df_merge, df_pivot, df_plot
```
High-level pandas wrappers for data manipulation and analysis.

### 8. SQLite Database
```
sqlite_query, sqlite_execute, sqlite_tables, sqlite_describe, sqlite_export
```
Embedded SQLite operations for local database management.

### 9. Apache Arrow / Parquet
```
arrow_read_parquet, arrow_read_csv, arrow_schema, arrow_filter, arrow_to_parquet
```
Columnar data processing with zero-copy reads.

### 10. Polars (fast DataFrames)
```
polars_read_csv, polars_query, polars_describe, polars_join, polars_export
```
Lightning-fast DataFrame operations via Polars.

### 11. Great Expectations
```
ge_validate, ge_create_suite, ge_run_checkpoint, ge_list_expectations
```
Data quality validation and profiling.

### 12. Matplotlib / Charts
```
chart_line, chart_bar, chart_scatter, chart_histogram, chart_save
```
Generate charts and save as images for reports.

---

## 🔐 Security & Penetration Testing

### 13. Pentest Tools ✅ (implemented)
```
pentest_portscan, pentest_service_enum, pentest_web_headers, pentest_ssl_check, pentest_dir_brute, pentest_whatweb, pentest_vuln_scan
```
Network scanning, service enumeration, and vulnerability detection.

### 14. Frida Dynamic Analysis ✅ (implemented)
```
frida_devices, frida_apps, frida_spawn, frida_attach, frida_unpin_ssl, frida_trace, frida_run_script
```
Mobile app runtime instrumentation and SSL pinning bypass.

### 15. Burp Suite API
```
burp_scan, burp_get_issues, burp_spider, burp_active_scan, burp_export_report
```
Automated web security scanning via Burp Suite REST API.

### 16. Nuclei Templates
```
nuclei_scan, nuclei_list_templates, nuclei_scan_url, nuclei_severity_filter
```
Fast vulnerability scanning with community templates.

### 17. Hashcat / Password Auditing
```
hash_identify, hash_crack, hash_benchmark, hash_wordlist_generate
```
Password hash identification and auditing.

### 18. YARA Rules
```
yara_scan_file, yara_scan_dir, yara_compile_rule, yara_match_memory
```
Malware pattern matching with YARA rules.

### 19. ClamAV
```
clam_scan_file, clam_scan_dir, clam_update_db, clam_quarantine
```
Open-source antivirus scanning.

### 20. Trivy (Container Security)
```
trivy_scan_image, trivy_scan_filesystem, trivy_scan_repo, trivy_list_vulns
```
Container and filesystem vulnerability scanning.

---

## 🔍 OSINT & Research

### 21. OSINT Recon ✅ (implemented)
```
osint_whois, osint_dns, osint_headers, osint_email_validate, osint_subdomain_enum, osint_ip_info, osint_social_check, osint_dorking
```
Domain, IP, email, and social media intelligence gathering.

### 22. Shodan
```
shodan_host, shodan_search, shodan_ports, shodan_vulns, shodan_honeypot_check
```
Internet-wide device search and enumeration.

### 23. VirusTotal
```
vt_scan_file, vt_scan_url, vt_get_report, vt_domain_info, vt_ip_info
```
Multi-engine malware and URL scanning.

### 24. Have I Been Pwned
```
hibp_check_email, hibp_check_password, hibp_breaches, hibp_paste_search
```
Credential breach checking.

### 25. Archive.org / Wayback Machine
```
wayback_search, wayback_get_snapshot, wayback_save, wayback_diff
```
Historical web page analysis and archiving.

### 26. SpiderFoot
```
spiderfoot_scan, spiderfoot_modules, spiderfoot_results, spiderfoot_correlate
```
Automated OSINT collection across 200+ data sources.

---

## ☁️ Cloud & Infrastructure

### 27. Supabase ✅ (implemented)
```
supa_query, supa_insert, supa_update, supa_delete, supa_rpc, supa_sql, supa_storage_list, supa_storage_upload, supa_storage_download
```
Full Supabase client — database CRUD, auth, storage, and edge functions.

### 28. AWS SDK (boto3)
```
aws_s3_list, aws_s3_upload, aws_s3_download, aws_ec2_list, aws_lambda_invoke, aws_cloudwatch_query
```
AWS service operations — S3, EC2, Lambda, CloudWatch.

### 29. Firebase / Firestore
```
firestore_get, firestore_set, firestore_query, firestore_delete, firebase_auth_user
```
Google Cloud Firestore document operations and auth management.

### 30. Cloudflare
```
cf_dns_list, cf_dns_create, cf_dns_delete, cf_workers_deploy, cf_analytics
```
Cloudflare DNS, Workers, and analytics management.

### 31. Terraform State
```
tf_state_list, tf_state_show, tf_plan_summary, tf_output, tf_workspace_list
```
Read and analyse Terraform state files.

### 32. Kubernetes
```
k8s_get_pods, k8s_get_services, k8s_logs, k8s_exec, k8s_apply, k8s_describe
```
Kubernetes cluster operations via kubectl.

### 33. Docker
```
docker_ps, docker_images, docker_logs, docker_exec, docker_build, docker_compose_up
```
Container lifecycle management.

### 34. Pulumi
```
pulumi_stack_list, pulumi_preview, pulumi_up, pulumi_outputs, pulumi_destroy
```
Infrastructure as code with Pulumi.

---

## 🐙 Version Control & CI/CD

### 35. GitHub API (Advanced)
```
gh_create_issue, gh_create_pr, gh_review_pr, gh_merge_pr, gh_list_actions, gh_trigger_workflow
```
Full GitHub API — issues, PRs, reviews, Actions, releases.

### 36. GitLab API
```
gitlab_create_issue, gitlab_create_mr, gitlab_pipelines, gitlab_deploy, gitlab_registry
```
GitLab CI/CD, merge requests, and container registry.

### 37. Bitbucket
```
bb_create_pr, bb_list_repos, bb_pipelines, bb_downloads
```
Bitbucket repository and pipeline management.

### 38. Jenkins
```
jenkins_build, jenkins_status, jenkins_logs, jenkins_queue, jenkins_config
```
Jenkins job triggering and monitoring.

### 39. ArgoCD
```
argo_apps, argo_sync, argo_status, argo_rollback, argo_diff
```
Kubernetes GitOps deployment management.

---

## 💬 Communication & Collaboration

### 40. Slack
```
slack_send, slack_channel_list, slack_channel_history, slack_thread_reply, slack_search
```
Send messages, read channels, search across Slack workspaces.

### 41. Discord
```
discord_send, discord_channel_messages, discord_create_thread, discord_reactions
```
Discord bot operations via webhooks and API.

### 42. Telegram
```
telegram_send, telegram_get_updates, telegram_send_photo, telegram_set_webhook
```
Telegram Bot API integration.

### 43. Email (SMTP + IMAP)
```
email_send, email_search, email_read, email_list_folders, email_move
```
Email operations — send via SMTP, search/read via IMAP.

### 44. Matrix / Element
```
matrix_send, matrix_rooms, matrix_read, matrix_join, matrix_create_room
```
Matrix protocol messaging.

### 45. Microsoft Teams
```
teams_send, teams_channels, teams_create_meeting, teams_list_chats
```
Teams messaging and meeting management.

---

## 🗄️ Databases

### 46. PostgreSQL
```
pg_query, pg_execute, pg_tables, pg_describe, pg_explain, pg_vacuum
```
Direct PostgreSQL operations via psycopg.

### 47. MySQL / MariaDB
```
mysql_query, mysql_execute, mysql_tables, mysql_describe, mysql_processlist
```
MySQL database operations.

### 48. MongoDB
```
mongo_find, mongo_insert, mongo_update, mongo_delete, mongo_aggregate, mongo_collections
```
MongoDB document operations.

### 49. Redis
```
redis_get, redis_set, redis_delete, redis_keys, redis_info, redis_pub, redis_sub
```
Redis key-value operations and pub/sub.

### 50. Elasticsearch
```
es_search, es_index, es_delete, es_bulk, es_indices, es_cluster_health
```
Elasticsearch full-text search and analytics.

### 51. Neo4j (Graph)
```
neo4j_query, neo4j_create_node, neo4j_create_rel, neo4j_shortest_path
```
Graph database operations with Cypher queries.

### 52. ClickHouse
```
ch_query, ch_insert, ch_tables, ch_describe, ch_partitions
```
Column-oriented analytics database.

### 53. Qdrant (Vector DB)
```
qdrant_search, qdrant_upsert, qdrant_collections, qdrant_delete, qdrant_scroll
```
Vector similarity search for embeddings.

### 54. Pinecone
```
pinecone_upsert, pinecone_query, pinecone_delete, pinecone_describe_index
```
Managed vector database for AI applications.

---

## 🤖 AI & ML

### 55. OpenAI API
```
openai_chat, openai_embed, openai_image, openai_tts, openai_whisper
```
OpenAI completions, embeddings, images, TTS, and transcription.

### 56. Anthropic Claude
```
claude_chat, claude_stream, claude_count_tokens
```
Anthropic Claude API for structured reasoning.

### 57. Hugging Face
```
hf_inference, hf_models_search, hf_dataset_load, hf_space_info
```
Hugging Face Inference API and model hub.

### 58. Ollama (Local LLMs)
```
ollama_chat, ollama_generate, ollama_embed, ollama_models, ollama_pull
```
Local LLM inference via Ollama.

### 59. LangChain / LlamaIndex
```
langchain_chain_run, langchain_rag_query, llamaindex_query, llamaindex_index
```
RAG pipeline and chain execution.

### 60. Stable Diffusion
```
sd_generate, sd_img2img, sd_inpaint, sd_models, sd_controlnet
```
Image generation via Stable Diffusion WebUI API.

---

## 📦 Package & Dependency Management

### 61. NPM Registry
```
npm_search, npm_info, npm_versions, npm_downloads, npm_audit
```
NPM package search, info, and vulnerability auditing.

### 62. PyPI
```
pypi_search, pypi_info, pypi_versions, pypi_dependencies, pypi_downloads
```
Python Package Index search and analysis.

### 63. Cargo (Rust)
```
cargo_search, cargo_info, cargo_audit, cargo_outdated
```
Rust crate search and security auditing.

### 64. Maven / Gradle
```
maven_search, maven_versions, maven_pom_parse, gradle_dependencies
```
Java dependency management and analysis.

---

## 🏠 Smart Home & IoT

### 65. Home Assistant
```
ha_states, ha_services, ha_call_service, ha_history, ha_automations
```
Home Assistant REST API — states, services, automations.

### 66. MQTT
```
mqtt_publish, mqtt_subscribe, mqtt_topics, mqtt_history
```
MQTT messaging for IoT devices.

### 67. Zigbee2MQTT
```
z2m_devices, z2m_state, z2m_set, z2m_permit_join
```
Zigbee device management.

### 68. Philips Hue
```
hue_lights, hue_set_light, hue_scenes, hue_groups, hue_sensor
```
Smart lighting control.

---

## 📱 Mobile & Desktop

### 69. ADB (Android Debug Bridge)
```
adb_devices, adb_shell, adb_install, adb_screenshot, adb_logcat, adb_pull, adb_push
```
Android device interaction via ADB.

### 70. Appium
```
appium_find, appium_tap, appium_swipe, appium_screenshot, appium_source
```
Mobile app UI automation.

### 71. macOS Automation
```
mac_notify, mac_screenshot, mac_clipboard, mac_open_app, mac_run_shortcut
```
macOS scripting via osascript/Shortcuts.

### 72. Windows Automation
```
win_registry, win_services, win_processes, win_screenshot, win_clipboard
```
Windows system management via PowerShell.

---

## 📄 Document & Media Processing

### 73. PDF Operations
```
pdf_extract_text, pdf_merge, pdf_split, pdf_to_images, pdf_metadata
```
PDF text extraction, merging, splitting.

### 74. Image Processing (PIL/Pillow)
```
img_resize, img_crop, img_convert, img_metadata, img_thumbnail, img_watermark
```
Image manipulation operations.

### 75. FFmpeg (Audio/Video)
```
ffmpeg_convert, ffmpeg_extract_audio, ffmpeg_thumbnail, ffmpeg_info, ffmpeg_trim
```
Media conversion and processing.

### 76. OCR (Tesseract)
```
ocr_image, ocr_pdf, ocr_screenshot, ocr_region
```
Optical character recognition.

### 77. Pandoc
```
pandoc_convert, pandoc_formats, pandoc_metadata
```
Universal document format conversion.

### 78. Excel (openpyxl)
```
excel_read, excel_write, excel_sheets, excel_formula, excel_chart
```
Excel spreadsheet operations.

---

## 🌐 Web & API

### 79. Playwright / Selenium
```
browser_goto, browser_click, browser_fill, browser_screenshot, browser_evaluate
```
Web browser automation for scraping and testing.

### 80. GraphQL Client
```
graphql_query, graphql_mutate, graphql_schema, graphql_introspect
```
GraphQL API interaction.

### 81. gRPC Client
```
grpc_call, grpc_stream, grpc_services, grpc_describe
```
gRPC service invocation.

### 82. WebSocket Client
```
ws_connect, ws_send, ws_receive, ws_close
```
WebSocket communication.

### 83. RSS/Atom Feed Reader
```
rss_parse, rss_latest, rss_search, atom_parse
```
RSS and Atom feed parsing and monitoring.

### 84. Webhooks
```
webhook_send, webhook_create_listener, webhook_history
```
Webhook sending and receiving.

---

## 📈 Monitoring & Observability

### 85. Prometheus
```
prom_query, prom_range_query, prom_targets, prom_alerts, prom_rules
```
Prometheus metric querying and alert management.

### 86. Grafana
```
grafana_dashboards, grafana_panels, grafana_annotations, grafana_alerts
```
Grafana dashboard and alert management.

### 87. Datadog
```
datadog_query, datadog_events, datadog_monitors, datadog_logs
```
Datadog monitoring and log analysis.

### 88. Sentry
```
sentry_issues, sentry_events, sentry_resolve, sentry_stats
```
Error tracking and resolution.

### 89. PagerDuty
```
pagerduty_incidents, pagerduty_acknowledge, pagerduty_resolve, pagerduty_oncall
```
Incident management and on-call scheduling.

---

## 🎮 Gaming & Automation

### 90. Steam API
```
steam_player, steam_games, steam_achievements, steam_market, steam_workshop
```
Steam profile, game, and market data.

### 91. Game Server (RCON)
```
rcon_command, rcon_players, rcon_status, rcon_ban
```
Game server remote administration.

---

## 💰 Finance & Crypto

### 92. CoinGecko
```
crypto_price, crypto_market, crypto_history, crypto_trending
```
Cryptocurrency prices and market data.

### 93. Stock Market (Yahoo Finance)
```
stock_price, stock_history, stock_news, stock_financials
```
Stock prices, history, and financial data.

### 94. Stripe
```
stripe_customers, stripe_charges, stripe_subscriptions, stripe_invoices
```
Payment processing and subscription management.

---

## 🏢 Project Management

### 95. Jira
```
jira_search, jira_create_issue, jira_update_issue, jira_transitions, jira_sprints
```
Jira issue tracking and sprint management.

### 96. Linear
```
linear_issues, linear_create, linear_update, linear_cycles, linear_projects
```
Linear project management operations.

### 97. Trello
```
trello_boards, trello_lists, trello_cards, trello_create_card, trello_move_card
```
Trello board and card management.

### 98. Asana
```
asana_tasks, asana_create_task, asana_update_task, asana_projects, asana_sections
```
Asana task and project operations.

---

## 🔧 System & Utilities

### 99. Cron Management
```
cron_list, cron_add, cron_remove, cron_edit, cron_next_run
```
System crontab management.

### 100. Systemd
```
systemd_status, systemd_start, systemd_stop, systemd_restart, systemd_logs, systemd_enable
```
Linux systemd service management.

---

## How to Create a Skill Tool

Every skill can ship tools by adding a `tools/` directory:

```
my-skill/
├── SKILL.md          # Required: skill instructions
└── tools/
    └── my_tools.py   # Required: must export TOOLS dict
```

The Python module must export a `TOOLS` dict:

```python
def my_function(arg: str) -> str:
    """Docstring — the agent reads this to understand the function."""
    return f"Result: {arg}"

def another_function(data: dict) -> dict:
    """Another tool available in the CodeAgent."""
    return {"processed": True, **data}

# This dict is required — keys become function names in CodeAgent
TOOLS = {
    "my_function": my_function,
    "another_function": another_function,
}
```

Then in the CodeAgent:

```python
# These functions are automatically available!
result = my_function("hello")
data = another_function({"key": "value"})
print(result, data)
```

### Design Guidelines

1. **Pure functions** — tools should be stateless where possible
2. **Graceful degradation** — handle missing dependencies with clear error messages
3. **Docstrings required** — the LLM reads them to understand usage
4. **No heavy imports at module level** — use lazy imports for optional dependencies
5. **Environment variables for config** — don't hardcode API keys or URLs
6. **Return strings or simple types** — the CodeAgent captures stdout and return values
7. **Timeout protection** — long-running operations should have configurable timeouts

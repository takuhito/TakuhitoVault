# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Repository: NotionLinker

- Purpose: Automate linking and maintenance between two Notion databases (Payments and DailyJournal). Creates missing journal pages, fixes titles/dates, removes/merges duplicates, and links payments to journals by date.
- Language/Runtime: Python 3 with virtualenv
- Entry points: Standalone scripts in the repo root; optional scheduler via launchd

Quick start
- Python venv and dependencies
  - python3 -m venv venv
  - source venv/bin/activate
  - pip install -r requirements.txt
- Environment
  - Copy and edit .env (see README.txt for details)
  - Key vars: NOTION_TOKEN, PAY_DB_ID, JOURNAL_DB_ID, DRY_RUN=true|false, NOTION_TIMEOUT, and optional property names (PROP_*) used by link_diary.py

Common commands
- One-off runs (DRY_RUN recommended first)
  - source venv/bin/activate
  - python link_diary.py
  - python create_missing_journal_pages.py
  - python notion_title_updater.py
  - python remove_duplicate_pages.py
  - python merge_duplicate_pages.py
- Scheduled run with notifications (Mac)
  - bash ./run_linker.sh
  - launchd (load/unload, uses com.tkht.notion-linker.plist)
    - launchctl unload ~/Library/LaunchAgents/com.tkht.notion-linker.plist 2>/dev/null || true
    - cp com.tkht.notion-linker.plist ~/Library/LaunchAgents/
    - launchctl load ~/Library/LaunchAgents/com.tkht.notion-linker.plist
    - logs: tail -f ~/Library/Logs/notion-linker.out.log ~/Library/Logs/notion-linker.err.log
- Optional Slack notifications
  - Set SLACK_WEBHOOK in .env for run_linker.sh to post success/failure messages

Notes on tests and linting
- No test suite or lint config is present. If you add tests, document how to run a single test here.

High-level architecture and data flow
- Shared patterns across scripts
  - Environment via python-dotenv; core vars: NOTION_TOKEN, JOURNAL_DB_ID, PAY_DB_ID
  - Notion client with timeout: Client(auth=NOTION_TOKEN, timeout_ms=NOTION_TIMEOUT*1000)
  - Robust API utilities: with_retry wrapper for timeout and rate limiting; iter_database_pages for paginated queries
  - DRY_RUN mode: prints intended mutations without calling Notion writes
- link_diary.py (primary linker)
  - Goal: Ensure each payment page (Payments DB) relates to the correct journal page (DailyJournal DB) by date
  - Inputs: Payments DB properties
    - PROP_PAY_DATE (e.g., 支払予定日)
    - PROP_MATCH_STR (e.g., 一致用日付) used as canonical match string; falls back to payment date if missing
    - PROP_REL_TO_JOURNAL (e.g., 日記[予定日]) relation to DailyJournal
    - JOURNAL side title property name (PROP_JOURNAL_TITLE; default: タイトル)
  - Algorithm
    - Query payment pages with date, optionally limited by RECHECK_DAYS
    - For each payment page:
      - Determine expected match string (PROP_MATCH_STR or derived from date)
      - Check existing relation; if present, retrieve the journal page and compare date-equivalent forms
        - Normalizes both "YYYY-MM-DD" and "YYYY-MMDD" to detect mismatches
      - If missing or mismatched relation:
        - Find journal by PROP_MATCH_STR equals first; if not found, find by exact title (normalized date form)
        - If still missing, create journal page with proper title; then set relation
    - Respects SLEEP_BETWEEN for rate-limit pacing
- notion_title_updater.py
  - Goal: Normalize journal page titles and optionally set a date property
  - Detects titles in "YYYY-MM-DD" and converts to "YYYY-MMDD"; extracts date to set the 日付 property when needed
  - Modes: title change, date-only fix, or both; interactive confirm unless DRY_RUN
- create_missing_journal_pages.py
  - Goal: Ensure a continuous range of dated journal pages exist
  - Computes date set for a configured period (hardcoded: from 2025-08-16 to 2027-03-31); compares to existing titles
  - Creates missing pages with title "YYYY-MMDD" and date property "YYYY-MM-DD"
- remove_duplicate_pages.py
  - Goal: For duplicate-titled journal pages, delete those without relations/URL/content
  - Checks a curated set of relation properties and presence of URL/body blocks as signals of content
  - Interactive confirm unless DRY_RUN
- merge_duplicate_pages.py
  - Goal: For duplicate-titled journal pages where multiple have content, merge into a single page
  - Merges relations (union) and keeps one URL value; copies child blocks from sources to target; archives sources
  - Interactive confirm unless DRY_RUN
- run_linker.sh (operational wrapper)
  - Loads .env, activates venv, runs link_diary.py, writes logs to ~/Library/Logs/
  - Notifies via macOS Notification Center (osascript) and optional Slack webhook
  - Prints short error snippet on failure and truncates old error logs on success
- launchd plists
  - com.tkht.notion-linker.plist: runs run_linker.sh at 0/15/30/45 minutes, on wake, and at load; writes logs to ~/Library/Logs
  - com.user.notion-linker.plist: alternate inline command version; includes placeholder EnvironmentVariables block

Configuration reference (from README.txt and scripts)
- Required in .env
  - NOTION_TOKEN, PAY_DB_ID, JOURNAL_DB_ID
- Optional/advanced
  - DRY_RUN=true|false, NOTION_TIMEOUT=seconds, RECHECK_DAYS, SLEEP_BETWEEN
  - PROP_PAY_DATE, PROP_MATCH_STR, PROP_REL_TO_JOURNAL, PROP_JOURNAL_TITLE

Operational tips specific to this repo
- First run with DRY_RUN=true to validate property names match your Notion DBs
- Property name defaults are Japanese (e.g., タイトル, 日付, 支払予定日); override via .env when your schema differs
- For scheduler setup, prefer com.tkht.notion-linker.plist unless you need inline env vars as in com.user.notion-linker.plist


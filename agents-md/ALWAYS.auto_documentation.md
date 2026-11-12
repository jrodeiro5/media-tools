# automatic documentation generation

- Write documentation in English unless explicitly asked otherwise
- Use markdown format (.md files)
- Use mermaid for diagrams
- Never hardwrap lines mid-sentence; let editors soft-wrap instead
- Code comments always in English; same for variables, functions, classes; (no need to change existing code)

## mandatory files

- **/README.md**: project introduction, features, configuration, launch, stop, log viewing
- **/docs/README.md**: document files in /docs, intended audience, classification (public|internal|confidential)
- **/docs/ARCHITECTURE.md**: main system architecture and major changes; update with significant modifications
- **/docs/PROJECT.md**: project definitions (sync with other systems) with frontmatter:
  ```
  ---
  id: XXX
  main_project_id: XXX      # if part of larger system
  title: xxx                # short description
  classification: xxx       # internal-cinfo, internal-client, public-access
  active: xxx               # true: in use, false: old repo
  people:
    technical_lead: email@cinfo.es
    product_owner: email@cinfo.es
  external_codes:
    mgt: XXX                # MGT system project code
    openproject: XXX        # projects.cinfo.es project id
    jira: XXX               # jira.cinfo.es project id
  main_git_branch: main     # name of the GIT branch for production code
  ---
  ```

## additional files, mandatory if the project is for an actual service, product or client project
- **/docs/release-notes.md**: changes per version (newest first) with date, version numbers, changes per component (max 10-15 words)
- **/docs/support-n1.md, support-n2.md, support-n3.md**:
  - **n1**: non-technical users; what to check, collect, when to escalate to n2
  - **n2**: CatServ stack operations (configuration, logs, health, integrations, documentation sync, webhooks, backups/restore, typical solutions)
  - **n3**: dev team; internal workings, data location, deployment/rollback, change locations
- **/docs/QA.md**: Q&A for all levels (end users, n1, n2, n3)
- **/docs/user-doc.md**: user manual; create separate user-doc-ROLExx.md for different roles
- **/docs/AI-usage.md**: table of IA models/algorithms used by final system (not dev/design) with security clearance
- **/docs/PERSONAL_DATA.md**: inventory of personal data processing (file must exist even if none); update when changes add/alter/remove data, fields, integrations, logs, analytics, vendors, or AI services. Include table with one row per processing activity and columns: processing name, purpose, legal basis (Art. 6 GDPR), data subject categories, data categories (flag Art. 9 special categories), data source, storage location (system, DB, path, country), retention period, recipients/processors (including non-EEA transfers), security measures, Cinfo's role (controller/processor), last review date, project owner, DPIA required status. Ask or mark pending for unknowns; never guess or include real personal data, only categories and example field names.
- **/TODO.md**: sections and tasks; keep in sync with external task systems; verify completed tasks

### other files

- REST API: **/docs/api/openapi.json**
- UI with prototype: documentation and interactive HTML at **/docs/design/** (not only external sites)
- Exported user manuals (if requested): **/docs/user-manuals/** with screenshots and all UI languages

[rev. 10]

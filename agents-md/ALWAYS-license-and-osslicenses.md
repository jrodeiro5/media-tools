## licenses: LICENSE.md, SBOM and CVE triage

- Project is property of Cinfo Contenidos Informativos Personalizados SL under closed source license for all custom code

- Add LICENSE.md to project root with a table listing all third-party open source software, licenses, and license links; organize by module with main dependencies and licenses; update whenever dependencies are added or removed;  use license IDs from https://spdx.org/licenses/ for opensource licenses if found there

- if project includes frontend/UI: convert LICENSE.md to HTML as oss-licenses.html with identical information in plain HTML format, include Cinfo copyright license, publish in frontend; update whenever dependencies are added or removed

- generate valid SPDX SBOMs files: use ISO/IEC 5962:2021 standard SPDX 3.0.1+ in JSON-LD and YAML versions generated; use https://spdx.cinfo.es as id prefix; name them "sbom.spdx.json" and "sbom.spdx.yml" and have them at the root of the project;  use official SPDX formats for objects  if available; when generating a new SBOM, include ALL components, direct AND transitive, in every programming language and in every shipped artifact:

  * Resolve the full dependency graph from lockfiles, never from manifests alone (package-lock.json / pnpm-lock.yaml / yarn.lock, poetry.lock / uv.lock / Pipfile.lock, go.sum + `go list -m all`, Cargo.lock, composer.lock, Gemfile.lock, packages.lock.json, `mvn dependency:tree` / `gradle dependencies`, etc.). If a module has no lockfile, generate one first (e.g. `pip-compile`, `npm install --package-lock-only`) and commit it.
  * Docker: build every image defined in the repo (Dockerfiles, docker-compose) and scan the built image of the final stage with an image-level SBOM tool (e.g. syft, trivy, cdxgen) using a docker run instead of installing it locally. Include OS packages (apt/apk/rpm), language packages installed at build time, and the base image (name, tag and sha256 digest). Pin base images by digest. Tools present only in intermediate build stages go in with build scope.
  * Components that no scanner detects (binaries downloaded with curl/wget, git clones, vendored or copied code, git submodules, scripts/fonts/assets loaded from a CDN in the frontend, ML models) must be declared explicitly, with name, version, download location, checksum and license. Keep them in `sbom-extra.yml` at the root, and merge that file into the generated SBOM.
  * Merge all sources (lockfiles + image scans + sbom-extra.yml) into the single root sbom.spdx.json / sbom.spdx.yml, deduplicating by purl.
  * Each software_Package must include version, `software_packageUrl` (purl), and a CPE when one exists (needed for automatic vulnerability matching), plus a declared license and a concluded license (SPDX IDs).
  * Model the graph with SPDX 3.0.1 relationships: root → direct deps via `dependsOn`, direct → transitive via `dependsOn`. Use LifecycleScopedRelationship with scope runtime / build / development / test. Set `completeness` on the relationships (`complete` when resolved from a lockfile or image, `incomplete` / `noAssertion` otherwise).
  * If a tool cannot emit SPDX 3.0.1 natively, generate in its native format and convert/merge into SPDX 3.0.1, then validate against the official SPDX 3.0.1 schema/SHACL shapes. Record the tools and versions used in the SBOM creationInfo.
  * LICENSE.md and oss-licenses.html must also cover transitive and OS-level components that are distributed (they may be grouped in a "Transitive dependencies" section per module/image). Flag any copyleft licenses (GPL, LGPL, AGPL, MPL…) found. 
  * If any component is AGPL, please do also ask the user to review it as this is a problem for Cinfo (would force us to publish the code of all the system using it) and explicitly document it as such, and who decided to keep it and why. 
  * For any new component found in the SBOM, try the CVE-SEARCH API at https://cvesearch.cinfo.es/api/ to look for CVEs with 8+ CVSS of used version. Check all found CVEs in one call: `https://cvesearch.cinfo.es/api-probability/?cve=CVE-X,CVE-Y,...&asset=<A>` (max 100 CVEs; `asset` = exposure: 1.0 public, 0.7 internal-cinfo or internal-client, 0.5 not yet in production, 0.2 if project not active). Sort results by `urgency` ascending, then `score` descending; report `urgency` and `deadline` for each. `urgency`: **1** actively exploited (CISA KEV), fix now or by KEV due date; **2** CVSS ≥ 7 and likely exploited (EPSS ≥ 0.1), fix within 15 days; **3** CVSS ≥ 7 or EPSS ≥ 0.1,
fix within 30 days; **4** normal patch cycle. Propose the user to update and test if urgent.

As all these will take a lot of time, alert the user about it and after the first time do it only after explicit version changes, not with all commits, and if possible, using a subagent.

[rev. 5]

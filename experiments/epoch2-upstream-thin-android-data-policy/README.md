# E2-R1/UT-4 — Android-mandatory data and writable-state policy

This experiment proves a host-neutral Android contract for CA trust, timezone data, temporary files, caches, bytecode, user site, venv state, and immutable installation behavior. The selected model uses three independent roots: a relocatable read-only Python install, an independently updateable data root, and a caller-owned app-private writable state root.

CA trust uses a bundled default with explicit `SSL_CERT_FILE` override. Timezone resolution uses a bundled raw zoneinfo tree through `PYTHONTZPATH`; implicit host discovery is rejected. Temp, cache, bytecode, opt-in user site, and venvs live under the writable state root. Fresh venvs after base movement are supported; pre-existing venvs remain base-bound unless separately proven.

The probe data is mechanism-only test data and is not a production CA or timezone selection. This authority enables Epoch 3 decisions but does not select a product, qualify broad devices, make the product selectable, or publish artifacts.

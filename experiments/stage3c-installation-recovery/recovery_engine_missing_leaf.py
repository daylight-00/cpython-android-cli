#!/usr/bin/env python3
from __future__ import annotations

import recovery_engine as frozen_engine
from recovery_operations_missing_leaf import install, uninstall

frozen_engine.install = install
frozen_engine.uninstall = uninstall


if __name__ == "__main__":
    raise SystemExit(frozen_engine.main())

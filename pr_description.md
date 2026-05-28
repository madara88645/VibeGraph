🎯 **What:** The testing gap addressed
Added a test (`test_cleanup_expired_upload_dirs_error_handling`) in `tests/test_upload.py` to ensure that if an `OSError` is raised while iterating over `os.scandir` entries during the cleanup of expired upload directories, the cleanup process correctly catches the exception and proceeds to process the subsequent entries instead of crashing.

📊 **Coverage:** What scenarios are now tested
The test covers the scenario where an intermediate file/directory yielded by `os.scandir` throws an `OSError` when its properties are accessed (e.g. via `.is_dir()`), confirming that the surrounding `try/except` block effectively suppresses the error and continues the loop.

✨ **Result:** The improvement in test coverage
Increased test suite robustness by explicitly verifying the safety net around temporary directory cleanup, guaranteeing that a single problematic temporary entry will not cause a memory leak by preventing the removal of other expired entries.

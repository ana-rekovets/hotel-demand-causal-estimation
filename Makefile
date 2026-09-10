.PHONY: help verify report rerun clean deps

NB     := notebooks/hotel_demand_estimation.ipynb
REPORT := report
DOC    := hotel_demand_estimation

help:
	@echo "  make verify   Check every number in the report against the notebook outputs"
	@echo "  make report   Verify, then rebuild the PDF"
	@echo "  make rerun    Re-execute the notebook and diff against committed results"
	@echo "                (needs EXPEDIA_PARQUET; see README)"

deps:
	pip install -r requirements.txt
	pip install nbclient nbformat ipykernel

verify:
	python3 scripts/check_report_matches_notebooks.py

report: verify
	cd $(REPORT) && pdflatex -interaction=nonstopmode $(DOC).tex >/dev/null && \
	                pdflatex -interaction=nonstopmode $(DOC).tex >/dev/null && \
	                rm -f *.aux *.log *.out *.toc
	@echo "rebuilt $(REPORT)/$(DOC).pdf"

rerun:
	@if [ -z "$$EXPEDIA_PARQUET" ]; then \
	    echo "EXPEDIA_PARQUET is not set."; \
	    echo "  EXPEDIA_PARQUET=/path/to/train_processed.parquet make rerun"; \
	    exit 1; \
	fi
	@mkdir -p build/rerun
	cd build/rerun && python3 ../../scripts/execute_notebook.py ../../$(NB) rerun.ipynb
	python3 scripts/compare_notebook_results.py $(NB) build/rerun/rerun.ipynb

clean:
	rm -rf build
	cd $(REPORT) && rm -f *.aux *.log *.out *.toc

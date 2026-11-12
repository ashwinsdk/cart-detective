# Workflow: Running the Full Pipeline and Regression Testing

This workflow guides running the complete research pipeline locally and validating the output.

## Steps

1. **Verify Services**:
   - Ensure backend API is operational: `curl http://localhost:8000/api/health`.
   - Ensure SearXNG is active if running with Docker Compose.
2. **Submit Test Query**:
   - Execute a test search via API or the Web UI:
     - Example: "riding jacket under 12000 INR"
3. **Monitor Execution Stream**:
   - Subscribe to the SSE stream at `/api/runs/{run_id}/stream`.
   - Validate that each stage transitions sequentially (Understand -> Discover -> Brand -> Scrape -> Reviews -> Verify -> Score -> Present).
4. **Validate Results**:
   - Verify that shortlisted products contain valid seller prices and source URLs.
   - Verify that any uncorroborated specification is flagged as "unverified".
   - Confirm that the UI renders cleanly with zero console warnings and no prohibited design elements.
5. **Inspect Persistence**:
   - Check that the search record, run metrics, and product shortlist are saved in `data/cart_detective.db`.

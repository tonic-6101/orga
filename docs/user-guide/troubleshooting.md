# Troubleshooting

Common issues and their solutions.

## Installation Issues

### "App not found" after installation

**Problem**: After running `bench install-app orga`, the app doesn't appear.

**Solution**:
1. Verify the app is installed:
   ```bash
   bench --site your-site list-apps
   ```
2. If not listed, check for installation errors:
   ```bash
   bench --site your-site install-app orga --verbose
   ```
3. Clear cache and restart:
   ```bash
   bench --site your-site clear-cache
   bench restart
   ```

### Migration errors

**Problem**: `bench migrate` fails with database errors.

**Solution**:
1. Check MariaDB is running
2. Verify database permissions
3. Try running with verbose output:
   ```bash
   bench --site your-site migrate --verbose
   ```

## Project Issues

### Cannot delete a project

**Problem**: Error when trying to delete a project.

**Cause**: Projects with linked tasks or milestones cannot be deleted.

**Solution**:
1. First delete or reassign all tasks linked to the project
2. Delete all milestones linked to the project
3. Then delete the project

### Project code already exists

**Problem**: Custom project code shows "duplicate" error.

**Solution**: Project codes must be unique. Either:
- Choose a different custom code, or
- Leave the field empty to auto-generate a unique code

## Task Issues

### Cannot set parent task

**Problem**: Error when selecting a parent task.

**Cause**: Circular references are not allowed. A task cannot be its own parent, and you cannot create loops (Task A → Task B → Task A).

**Solution**: Review your task hierarchy and ensure there are no circular references.

### Completion date not updating

**Problem**: Task marked as completed but completion date is empty.

**Solution**: The completion date is set when the status changes TO "Completed". If you created the task with status already set to "Completed", save it, then edit and save again.

## Permission Issues

### "Not permitted" error

**Problem**: User receives permission error when accessing Orga.

**Solution**:
1. Verify the user has either "Orga Manager" or "Orga User" role
2. Check role assignment:
   - Go to User → [Username] → Roles
   - Add the appropriate Orga role
3. Clear user cache:
   ```bash
   bench --site your-site clear-cache
   ```

### Cannot delete others' tasks

**Problem**: Orga User cannot delete tasks created by others.

**Cause**: This is expected behavior. Orga Users can only delete tasks they own.

**Solution**: Either:
- Ask the task owner to delete it
- Have an Orga Manager delete it
- Request Orga Manager role if needed

## Health Issues

### Project health not updating

**Problem**: Project health status seems outdated.

**Cause**: Health is automatically recalculated every 4 hours.

**Solution**:
1. Wait for the next scheduled update, or
2. Trigger a manual recalculation via API:
   ```javascript
   frappe.call({method: 'orga.orga.api.dashboard.recalculate_project_health', args: {project_name: 'ORG-2026-0001'}})
   ```
3. Verify the scheduler is running:
   ```bash
   bench --site your-site scheduler status
   ```

### All projects showing "Unknown" health

**Problem**: Every project shows Unknown instead of Green/Yellow/Red.

**Cause**: Health calculation hasn't run yet.

**Solution**:
1. Ensure the scheduler is enabled:
   ```bash
   bench --site your-site scheduler enable
   ```
2. Trigger manual calculation for all projects:
   ```python
   from orga.orga.services.health_calculator import update_all_project_health
   update_all_project_health()
   ```

### Health shows Red but project seems fine

**Problem**: A project shows Red health but appears to be progressing normally.

**Possible causes**:
1. Overdue tasks exist but aren't visible (check filters)
2. Budget spent exceeds expected for current progress
3. Missed milestones from earlier phases

**Solution**:
1. Check the health breakdown via API to see which factor is causing the low score
2. Review overdue tasks and either complete or reschedule them
3. Update milestone statuses if any were missed
4. Verify budget and spending data is accurate

## API Issues

### API returns empty results

**Problem**: API calls return empty data.

**Possible causes**:
1. No data exists yet
2. Filter parameters are too restrictive
3. Permission issues

**Solution**:
1. Verify data exists via Frappe desk
2. Try API without filters first
3. Check user has read permission on the DocType

### "Method not whitelisted" error

**Problem**: API call fails with whitelisting error.

**Solution**: Ensure you're using the correct method path:
```python
# Correct
frappe.call("orga.orga.api.project.get_projects")

# Incorrect
frappe.call("orga.api.project.get_projects")
```

## Performance Issues

### Slow dashboard loading

**Problem**: Dashboard takes a long time to load.

**Possible causes**: Large number of tasks/projects.

**Solution**:
1. Use pagination in API calls (limit/offset parameters)
2. Archive completed projects periodically
3. Check database indexes are properly created

## Getting More Help

If your issue isn't listed here:

1. Check the [FAQ](faq.md) for common questions
2. Review the [API documentation](../developer-guide/API.md) for technical details
3. Search or create an issue on [GitHub](https://github.com/your-org/orga/issues)

When reporting issues, please include:
- Frappe version (`bench version`)
- Orga version (in VERSION file)
- Steps to reproduce the issue
- Any error messages (full traceback if available)

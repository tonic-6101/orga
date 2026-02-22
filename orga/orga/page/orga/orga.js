frappe.pages['orga'].on_page_load = function(wrapper) {
	frappe.orga_page = new OrgaPage(wrapper);
};

frappe.pages['orga'].refresh = function(wrapper) {
	if (frappe.orga_page) {
		frappe.orga_page.refresh();
	}
};

class OrgaPage {
	constructor(wrapper) {
		this.wrapper = $(wrapper);
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __('Orga'),
			single_column: true
		});

		// Hide default page header for custom layout
		$(wrapper).find('.page-head').hide();

		this.selected_item = null;
		this.active_tab = 'plan';
		this.make();
	}

	make() {
		this.wrapper.find('.layout-main-section').html(frappe.render_template('orga'));
		this.$container = this.wrapper.find('.orga-dashboard-container');

		this.setup_components();
		this.bind_events();
		this.load_sample_data();
	}

	refresh() {
		// Refresh data if needed
	}

	setup_components() {
		this.$tree_container = this.$container.find('.orga-tree-container');
		this.$gantt_container = this.$container.find('.orga-gantt-container');
		this.$inspector = this.$container.find('.orga-inspector');
		this.$details_container = this.$container.find('.orga-details-table-container');
	}

	// Sample project data
	get_sample_data() {
		return [
			{
				id: 'project-1',
				name: 'Einfamilienhaus',
				type: 'project',
				start_date: '2025-03-23',
				duration: 19,
				progress: 60,
				children: [
					{
						id: 'phase-1',
						name: 'Vorplanung',
						type: 'phase',
						start_date: '2025-03-24',
						duration: 8,
						progress: 100,
						children: [
							{
								id: 'task-1',
								name: 'Grundriss erstellen',
								type: 'task',
								start_date: '2025-03-24',
								duration: 4,
								progress: 100
							},
							{
								id: 'task-2',
								name: 'Statik berechnen',
								type: 'task',
								start_date: '2025-03-28',
								duration: 4,
								progress: 80
							}
						]
					}
				]
			},
			{
				id: 'project-2',
				name: 'Bürogebäude',
				type: 'project',
				start_date: '2025-03-24',
				duration: 30,
				progress: 20,
				children: []
			},
			{
				id: 'project-3',
				name: 'Lagerhalle',
				type: 'project',
				start_date: '2025-04-01',
				duration: 45,
				progress: 0,
				children: []
			}
		];
	}

	load_sample_data() {
		this.data = this.get_sample_data();
		this.render_tree(this.data);
		this.render_gantt(this.flatten_data(this.data));
		this.render_details_table(this.flatten_data(this.data));

		// Select first item by default
		if (this.data.length > 0) {
			this.select_item(this.data[0].id);
		}
	}

	flatten_data(data, level = 0, result = []) {
		data.forEach(item => {
			result.push({ ...item, level });
			if (item.children && item.children.length) {
				this.flatten_data(item.children, level + 1, result);
			}
		});
		return result;
	}

	render_tree(data) {
		const html = this.build_tree_html(data);
		this.$tree_container.html(`
			<table class="orga-tree-table">
				<thead>
					<tr>
						<th class="tree-col">Name</th>
						<th class="date-col">Startzeit</th>
						<th class="duration-col">Dauer</th>
					</tr>
				</thead>
				<tbody>
					${html}
				</tbody>
			</table>
		`);
	}

	build_tree_html(data, level = 0) {
		let html = '';
		data.forEach(item => {
			const has_children = item.children && item.children.length > 0;
			const icon = item.type === 'project' ? 'folder' :
			             item.type === 'phase' ? 'folder-open' : 'file-alt';
			const padding = level * 20;
			const formatted_date = this.format_date(item.start_date);

			html += `
				<tr class="orga-tree-row" data-id="${item.id}" data-level="${level}">
					<td class="tree-col">
						<div class="tree-cell" style="padding-left: ${padding}px;">
							${has_children ? '<span class="tree-toggle"><i class="fa fa-caret-down"></i></span>' : '<span class="tree-toggle-spacer"></span>'}
							<i class="fa fa-${icon} tree-icon"></i>
							<span class="tree-label">${item.name}</span>
						</div>
					</td>
					<td class="date-col">${formatted_date}</td>
					<td class="duration-col">${item.duration} Tage</td>
				</tr>
			`;

			if (has_children) {
				html += this.build_tree_html(item.children, level + 1);
			}
		});
		return html;
	}

	format_date(date_str) {
		if (!date_str) return '';
		const date = new Date(date_str);
		const day = String(date.getDate()).padStart(2, '0');
		const month = String(date.getMonth() + 1).padStart(2, '0');
		const year = date.getFullYear();
		return `${day}.${month}.${year}`;
	}

	render_gantt(tasks) {
		const start_date = new Date('2025-03-23');
		const num_days = 14;
		const days = [];

		for (let i = 0; i < num_days; i++) {
			const d = new Date(start_date);
			d.setDate(d.getDate() + i);
			days.push(d);
		}

		let header_html = '<div class="gantt-header"><div class="gantt-header-row">';
		days.forEach(day => {
			const dayNum = day.getDate();
			const month = day.toLocaleDateString('de-DE', { month: 'short' });
			const isWeekend = day.getDay() === 0 || day.getDay() === 6;
			header_html += `<div class="gantt-day-col ${isWeekend ? 'weekend' : ''}">${dayNum} ${month}</div>`;
		});
		header_html += '</div></div>';

		let body_html = '<div class="gantt-body">';
		tasks.forEach(task => {
			const task_start = new Date(task.start_date);
			const offset_days = Math.max(0, (task_start - start_date) / (1000 * 60 * 60 * 24));
			const bar_width = Math.min(task.duration, num_days - offset_days);
			const bar_color = task.type === 'project' ? 'project' :
			                  task.type === 'phase' ? 'phase' : 'task';

			body_html += `
				<div class="gantt-row" data-id="${task.id}">
					<div class="gantt-bar-container">
						${bar_width > 0 ? `
							<div class="gantt-bar ${bar_color}" style="left: ${offset_days * (100/num_days)}%; width: ${bar_width * (100/num_days)}%;">
								<div class="gantt-bar-progress" style="width: ${task.progress}%"></div>
								<span class="gantt-bar-label">${task.name}</span>
							</div>
						` : ''}
					</div>
				</div>
			`;
		});
		body_html += '</div>';

		this.$gantt_container.html(header_html + body_html);
	}

	render_details_table(data) {
		const columns = ['Titel', 'Typ', 'Start', 'Dauer', 'Fortschritt'];

		let html = `
			<table class="orga-details-table">
				<thead>
					<tr>
						${columns.map(col => `<th>${col}</th>`).join('')}
					</tr>
				</thead>
				<tbody>
					${data.map(item => `
						<tr data-id="${item.id}">
							<td>${item.name || ''}</td>
							<td><span class="type-badge ${item.type}">${item.type}</span></td>
							<td>${this.format_date(item.start_date)}</td>
							<td>${item.duration} Tage</td>
							<td>
								<div class="progress-cell">
									<div class="progress-bar-mini">
										<div class="progress-fill" style="width: ${item.progress}%"></div>
									</div>
									<span>${item.progress}%</span>
								</div>
							</td>
						</tr>
					`).join('')}
				</tbody>
			</table>
		`;

		this.$details_container.html(html);
	}

	bind_events() {
		const me = this;

		// Tree row selection
		this.$container.on('click', '.orga-tree-row', function() {
			const id = $(this).data('id');
			me.select_item(id);
		});

		// Tree toggle
		this.$container.on('click', '.tree-toggle', function(e) {
			e.stopPropagation();
			const row = $(this).closest('.orga-tree-row');
			const level = parseInt(row.data('level'));
			const is_collapsed = $(this).hasClass('collapsed');

			$(this).toggleClass('collapsed');
			$(this).find('i').toggleClass('fa-caret-down fa-caret-right');

			let next = row.next();
			while (next.length && parseInt(next.data('level')) > level) {
				if (is_collapsed) {
					next.show();
				} else {
					next.hide();
				}
				next = next.next();
			}
		});

		// Gantt row click
		this.$container.on('click', '.gantt-row', function() {
			const id = $(this).data('id');
			me.select_item(id);
		});

		// Details table row click
		this.$container.on('click', '.orga-details-table tbody tr', function() {
			const id = $(this).data('id');
			me.select_item(id);
		});

		// Inspector tabs
		this.$container.on('click', '.orga-tab-btn', function() {
			me.$container.find('.orga-tab-btn').removeClass('active');
			$(this).addClass('active');
			me.active_tab = $(this).data('tab');
			me.update_inspector_content();
		});

		// View toggle buttons
		this.$container.on('click', '.orga-view-toggle .btn', function() {
			me.$container.find('.orga-view-toggle .btn').removeClass('active');
			$(this).addClass('active');
			const view = $(this).data('view');
			me.switch_view(view);
		});

		// Details panel toggle
		this.$container.on('click', '.orga-btn-details', function() {
			$(this).toggleClass('active');
			me.$container.find('.orga-details-panel').toggleClass('collapsed');
		});

		// New button
		this.$container.on('click', '.orga-btn-new', function() {
			frappe.new_doc('Orga Project');
		});

		// Inspector form changes
		this.$container.on('change', '.orga-inspector input, .orga-inspector select', function() {
			me.on_inspector_change($(this));
		});

		// Global search
		this.$container.on('click', '.orga-search-btn', function() {
			me.perform_search();
		});

		this.$container.on('keypress', '.orga-search-input', function(e) {
			if (e.which === 13) {
				me.perform_search();
			}
		});
	}

	perform_search() {
		const category = this.$container.find('.orga-search-category').val();
		const query = this.$container.find('.orga-search-input').val().toLowerCase().trim();

		if (!query) {
			// Reset to show all items
			this.render_tree(this.data);
			this.render_gantt(this.flatten_data(this.data));
			this.render_details_table(this.flatten_data(this.data));
			return;
		}

		// Filter data based on search
		const filtered_data = this.filter_data(this.data, query, category);

		// Re-render with filtered data
		this.render_tree(filtered_data);
		this.render_gantt(this.flatten_data(filtered_data));
		this.render_details_table(this.flatten_data(filtered_data));
	}

	filter_data(data, query, category) {
		const result = [];

		for (const item of data) {
			// Check if item matches category filter
			if (category && item.type !== category) {
				// Still check children
				if (item.children && item.children.length) {
					const filtered_children = this.filter_data(item.children, query, category);
					if (filtered_children.length) {
						result.push({ ...item, children: filtered_children });
					}
				}
				continue;
			}

			// Check if item name matches query
			const matches = item.name.toLowerCase().includes(query);

			if (matches) {
				// Include item with all its children
				result.push({ ...item });
			} else if (item.children && item.children.length) {
				// Check children
				const filtered_children = this.filter_data(item.children, query, category);
				if (filtered_children.length) {
					result.push({ ...item, children: filtered_children });
				}
			}
		}

		return result;
	}

	select_item(id) {
		this.selected_item = id;

		// Highlight in tree
		this.$container.find('.orga-tree-row').removeClass('selected');
		this.$container.find(`.orga-tree-row[data-id="${id}"]`).addClass('selected');

		// Highlight in gantt
		this.$container.find('.gantt-row').removeClass('selected');
		this.$container.find(`.gantt-row[data-id="${id}"]`).addClass('selected');

		// Highlight in details table
		this.$container.find('.orga-details-table tbody tr').removeClass('selected');
		this.$container.find(`.orga-details-table tbody tr[data-id="${id}"]`).addClass('selected');

		// Update inspector
		const item = this.find_item_by_id(this.data, id);
		if (item) {
			this.update_inspector(item);
		}
	}

	find_item_by_id(data, id) {
		for (const item of data) {
			if (item.id === id) return item;
			if (item.children) {
				const found = this.find_item_by_id(item.children, id);
				if (found) return found;
			}
		}
		return null;
	}

	update_inspector(item) {
		// Update header
		this.$container.find('.orga-inspector-title .context-name').text(`(${item.name})`);

		// Update form fields
		this.$container.find('#inspector-titel').val(item.name || '');
		this.$container.find('#inspector-untertitel').val(item.type || '');
		this.$container.find('#inspector-start-date').val(item.start_date || '');
		this.$container.find('#inspector-duration').val(item.duration || '');
		this.$container.find('#inspector-progress').val(item.progress || 0);

		// Update progress display
		this.$container.find('.progress-value').text(`${item.progress || 0}%`);
		this.$container.find('.inspector-progress-bar .progress-fill').css('width', `${item.progress || 0}%`);
	}

	update_inspector_content() {
		// Switch content based on active tab
		const tab_contents = {
			'plan': 'Plan details',
			'links': 'Links and dependencies',
			'layers': 'Layers and hierarchy',
			'edit': 'Edit mode'
		};
		// Tab content switching can be implemented here
	}

	on_inspector_change($field) {
		if (!this.selected_item) return;

		const item = this.find_item_by_id(this.data, this.selected_item);
		if (!item) return;

		const field_id = $field.attr('id');
		const value = $field.val();

		// Update item data based on field
		switch (field_id) {
			case 'inspector-titel':
				item.name = value;
				break;
			case 'inspector-progress':
				item.progress = parseInt(value) || 0;
				this.$container.find('.progress-value').text(`${item.progress}%`);
				this.$container.find('.inspector-progress-bar .progress-fill').css('width', `${item.progress}%`);
				break;
		}

		// Re-render affected components
		this.render_tree(this.data);
		this.render_gantt(this.flatten_data(this.data));
		this.render_details_table(this.flatten_data(this.data));

		// Re-select item to maintain highlight
		this.select_item(this.selected_item);
	}

	switch_view(view) {
		if (view === 'list') {
			this.$container.find('.orga-gantt-panel').hide();
			this.$container.find('.orga-tree-panel').css('flex', '1');
		} else {
			this.$container.find('.orga-gantt-panel').show();
			this.$container.find('.orga-tree-panel').css('flex', '');
		}
	}
}

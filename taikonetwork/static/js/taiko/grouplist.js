// Load the Visualization API and the controls package.
google.load('visualization', '1.0', {'packages':['controls']});

// Set a callback to run when the Google Visualization API is loaded.
google.setOnLoadCallback(drawGroupList);

function drawGroupList() {
  var data = new google.visualization.DataTable();
  data.addColumn('string', 'Name');
  data.addColumn('string', 'Type');
  data.addColumn('string', 'Website');
  data.addColumn('string', 'City');
  data.addColumn('string', 'State/Province');
  data.addColumn('string', 'Country');
  data.addColumn('date', 'Founding Year');
  
  var i, year, groupdata;
  var numGroups = groups.length;
  for (i = 0; i < numGroups; i++) {
    if (! groups[i]['year']) {
      year = {v: new Date(1950, 1, 1), f: ''}
    } else {
      year = {v: new Date(groups[i]['year'], 1, 1),
              f: groups[i]['year'].toString()};
    }
    groupdata = [groups[i]['name'], groups[i]['category'], groups[i]['website'],
                 groups[i]['city'], groups[i]['state'], groups[i]['country'],
                 year];
    data.addRow(groupdata);
  };

  var dashboard = new google.visualization.Dashboard(document.getElementById('dashboard_div'));
  
  var nameFilter = new google.visualization.ControlWrapper({
    controlType: 'StringFilter',
    containerId: 'name_filter_div',
    options: {
      filterColumnLabel: 'Name',
      matchType: 'any',
      ui: {label: 'Name', labelSeparator: ':'}
    }
  });
  var countryFilter = new google.visualization.ControlWrapper({
    controlType: 'CategoryFilter',
    containerId: 'country_filter_div',
    options: {
      filterColumnLabel: 'Country',
      ui: {
        label: 'Country',
        labelSeparator: ':',
        allowMultiple: false,
        caption: 'Search or choose a value...'
      }
    }
  });
  var stateFilter = new google.visualization.ControlWrapper({
    controlType: 'StringFilter',
    containerId: 'state_filter_div',
    options: {
      filterColumnLabel: 'State/Province',
      matchType: 'any',
      ui: {
        label: 'State/Province',
        labelSeparator: ':'
      }
    }
  });
  var cityFilter = new google.visualization.ControlWrapper({
    controlType: 'StringFilter',
    containerId: 'city_filter_div',
    options: {
      filterColumnLabel: 'City',
      matchType: 'any',
      ui: {label: 'City', labelSeparator: ':'}
    }
  });

  var catFilter = new google.visualization.ControlWrapper({
    controlType: 'CategoryFilter',
    containerId: 'type_filter_div',
    options: {
      filterColumnLabel: 'Type',
      ui: {
        label: 'Type',
        labelSeparator: ':',
        caption: 'Search or choose a value...'
      }
    }
  });
  
  var rangeFilter = new google.visualization.ControlWrapper({
    controlType: 'DateRangeFilter',
    containerId: 'range_filter_div',
    options: {
      filterColumnLabel: 'Founding Year',
      ui: {
        label: 'Founding Year',
        labelSeparator: ':',
        format: { pattern: 'yyyy' }
      }
    }
  });

  var groupTable = new google.visualization.ChartWrapper({
    chartType: 'Table',
    containerId: 'table_div',
    options: {
      title: 'Taiko Groups',
      showRowNumber: true
    }
  });

  dashboard.bind([nameFilter, countryFilter, stateFilter, cityFilter,
                  rangeFilter, catFilter], [groupTable]);
  dashboard.draw(data);
}

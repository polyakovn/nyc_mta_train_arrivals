document.addEventListener('DOMContentLoaded', function() {
  $('#line_selector').hide();
  var dt = new Date();
  var cur_time = dt.toLocaleTimeString();
  $('#current_time').text("It is currently " + cur_time);
}, false);


function get_station_info() {
  $('#line_selector').find('option').remove().end().append('<option>--Line--</option>');
  var station = document.getElementById("station");
  var selected_station = station.options[station.selectedIndex].text;
  $.get('/station_info', {'station':selected_station} , function(train_list) {
    var line_set = make_table(train_list);
    add_line_options(line_set);
    $('#line_selector').show();
  });
}

function make_table(train_list) {
  $('#times tr').remove();
  $('#times').append('<tr><th>Line</th><th>Direction</th><th>Next Arrivals (in minutes from now)</th></tr>')
  var line_set = new Set();
  for(train in train_list) {
    let key = train.split(" ");
    let line = key[1];
    let dir = key[0].slice(-1);
    let direction = dir == 'S' ? 'South' : 'North';
    let arrival_times = train_list[train].slice(0,3);
    add_station_row(line, direction, arrival_times);
    line_set.add(line);
  }
  return line_set;
}

function add_line_options(line_set) {
  for (let line of line_set.keys()) {
    $("#line_selector").append('<option>' + line + '</option>');
  }
}

function add_station_row(line, direction, arrival_times) {
  var table = document.getElementById("times");
  var row = table.insertRow(-1);
  var line_cell = row.insertCell(0);
  var direction_cell = row.insertCell(1);
  var times_cell = row.insertCell(2);
  line_cell.innerHTML = line;
  direction_cell.innerHTML = direction;
  times_cell.innerHTML = arrival_times;
}

function filter_by_line(){
  var station = document.getElementById("station");
  var selected_station = station.options[station.selectedIndex].text;
  var lines = document.getElementById("line_selector");
  var line = lines.options[lines.selectedIndex].text;
  if(line != '--Line--'){
    $.get('/line_station_info', {'station':selected_station, 'line': line}, function(train_list) {
      make_table(train_list);
    });
  } else {
    $.get('/station_info', {'station':selected_station}, function(train_list) {
      make_table(train_list);
    });
  }
}

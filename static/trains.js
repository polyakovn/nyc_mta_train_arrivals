document.addEventListener('DOMContentLoaded', function() {
  $('#line_selector').hide();
  $('#direction_selector').hide();
  var dt = new Date();
  var cur_time = dt.toLocaleTimeString();
  $('#current_time').text("It is currently " + cur_time);
}, false);

function get_station_info() {
  var selected_station = $('#station').find(":selected").text();
  console.log($('#station').find(":selected").data("latitude"));
  $.get('/station_info', {'station':selected_station} , function(train_info) {
    try {
      var trains = JSON.parse(train_info);
      display_results(trains);
    }
    catch(error) {
      console.log(error);
      alert("Sorry, it seems like the data for this station is currently unavailable. Try again in a few minutes!");
    }
  });
}


function display_results(trains) {
  $('#times tr').remove();
  $('#times').append('<tr><th>Line</th><th>Direction</th><th>Next Arrivals (in minutes from now)</th></tr>')
  for(train in trains) {
    add_station_row(trains[train].line, trains[train].direction, trains[train].arrival_times);
  }
  display_line_filter(trains);
  $("#direction_selector").show();
}

function display_line_filter(trains) {
  if ($('#line_selector').find(":selected").text() == '--Line--'){
    $('#line_selector').find('option').remove().end().append('<option>--Line--</option>')
    var station_lines = get_line_options(trains);
    add_line_options(station_lines);
  }
  $("#line_selector").show();
}

function get_line_options(trains) {
  station_lines = new Set();
  for(train in trains) {
    station_lines.add(trains[train].line);
  }
  return station_lines;
}

function add_line_options(station_lines) {
  for (let line of station_lines.keys()) {
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
  times_cell.innerHTML = arrival_times.slice(0,3);
}

function add_filter(){
  var station = $('#station').find(":selected").text();
  var line = $('#line_selector').find(":selected").text();
  var direction= $('#direction_selector').find(":selected").text();
  if(line != '--Line--' && direction != '--Direction--'){
    filter_by_line_and_direction(station, line, direction);
  } else if (line != '--Line--') {
    filter_by_line(station, line);
  } else if (direction != '--Direction--') {
    filter_by_direction(station, direction);
  } else {
    get_station_info();
  }
}

function filter_by_line_and_direction(station, line, direction){
  $.get('/filter_by_line_and_direction', {'station':station, 'line':line, 'direction':direction}, function(train_info) {
    var trains = JSON.parse(train_info);
    display_results(trains);
  });
}


function filter_by_line(station, line){
  $.get('/filter_by_line', {'station':station, 'line':line}, function(train_info) {
    var trains = JSON.parse(train_info);
    display_results(trains);
  });
}

function filter_by_direction(station, direction){
  $.get('/filter_by_direction', {'station':station, 'direction':direction}, function(train_info) {
    var trains = JSON.parse(train_info);
    display_results(trains);
  });
}

function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((position)=> {
            console.log(position.coords.latitude);
            console.log(position.coords.longitude);
        });
    } else {
        x.innerHTML = "Geolocation is not supported by this browser.";
    }
}



function sort() {
  if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((position)=> {
        var select = $('#station');
        var options_list = select.find('option');
        const cur_latitude = position.coords.latitude;
        const cur_longitude = position.coords.longitude;
        options_list.sort((a,b) => {
          const a_latitude = a.getAttribute('data-latitude');
          const a_longitude = a.getAttribute('data-longitude');
          const b_latitude = b.getAttribute('data-latitude');
          const b_longitude = b.getAttribute('data-longitude');
          const a_distance = getDistanceFromLatLonInKm(cur_latitude,cur_longitude,a_latitude,a_longitude);
          const b_distance = getDistanceFromLatLonInKm(cur_latitude,cur_longitude,b_latitude,b_longitude);
          console.log(a_distance, b_distance, a.innerHTML, b.innerHTML);
          return (a_distance > b_distance ? 1: -1);
        });
        select.html('').append(options_list);
        $("#station").val(options_list[0].innerHTML);
        get_station_info()
      });
  } else {
      x.innerHTML = "Geolocation is not supported by this browser.";
  }
}

function getDistanceFromLatLonInKm(lat1,lon1,lat2,lon2) {
  var R = 6371; // Radius of the earth in km
  var dLat = deg2rad(lat2-lat1);  // deg2rad below
  var dLon = deg2rad(lon2-lon1);
  var a =
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) *
    Math.sin(dLon/2) * Math.sin(dLon/2)
    ;
  var c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  var d = R * c; // Distance in km
  return d;
}

function deg2rad(deg) {
  return deg * (Math.PI/180)
}

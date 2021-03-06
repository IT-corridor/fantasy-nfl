var slate, games;

filterTable = function () {
  var position = $('.position-filter .nav-item a.active').html(),
      keyword = $('#search-player').val().toLowerCase().trim();    

  if (position == 'All') {
    position = '';
  } else if (position == 'DEF') {
    position = 'D';
  }

  $(".player-list tr").filter(function() {
    $(this).toggle($(this).find('td:nth-child(2)').text().indexOf(position) > -1 && $(this).find('td:nth-child(1)').text().toLowerCase().indexOf(keyword) > -1)
  });

  $(".player-list thead tr").filter(function() {
    $(this).toggle(true);
  });
}

filterTable();

$(function() {
  $('.nav-tabs.ds .nav-link:first').click();


  // filter players
  $("#search-player").on("keyup", function() {
    filterTable();
  });

  $("#search-player").on("search", function() {
    filterTable();
  });

  $('.position-filter .nav-item a').on('click', function() {
    $('.position-filter .nav-item a').removeClass('active');
    $(this).toggleClass('active');
    filterTable();
  })
})

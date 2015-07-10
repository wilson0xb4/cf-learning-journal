// $( "article" ).click(function() {
//   $( this ).replaceWith( function(e) {

//       $.ajax({
//         method: 'GET',
//         url: '/add'
//       })

//   })
// })


// show add form
$('#add').click(function(e) {
  e.preventDefault();

  $.ajax({
            method: "GET",
            url: '/add'
        })
        .done(function(response) {
            // make DOM-able!-ish...
            $html = $($.parseHTML( response ));
            addForm = $html.find('form');

            // flip current link selection
            $("#list").removeClass("current");
            $("#add").addClass("current");

            // swap content
            $("#ajax-container").replaceWith( addForm );

        })

})


// show update form, populated with the entry
$('#edit_link').click(function(e) {
  // e.preventDefault();
  e.stopImmediatePropagation()

  $.ajax({
        // var entry_id = $("#edit_link").attr("href").match(/[0-9]+/)[1];

            method: "GET",
            url: '/update/' + entry_id
        })
        // .done(function(response) {
            // // make DOM-able!-ish...
            // $html = $($.parseHTML( response ));
            // addForm = $html.find('form');

            // // flip current link selection
            // $("#list").removeClass("current");
            // $("#add").addClass("current");

            // // swap content
            // $("#ajax-container").replaceWith( "addForm" );

        // })

})

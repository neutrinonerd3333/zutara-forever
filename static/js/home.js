$(document).ready(function(){

	var last_item = $(".list li:last-child input");
	$(".list li:last-child input").last().click(function(){
		$(".list ul").append('<li><input type="text"></li>');
		last_item = $(".list li:last-child input");
	});
});
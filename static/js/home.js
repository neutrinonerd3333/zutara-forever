$(document).ready(function(){

	var last_item = $(".list li:last-child");
	last_item.click(function(){
		last_item.before('<li><input type="text"></li>');
	});
});
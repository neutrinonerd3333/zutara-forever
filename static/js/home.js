$(document).ready(function(){

    // upon clicking the last li in the list, a new li will be 
    // formed right above it (so last li remains last)
	var last_item = $(".list li:last-child");
	last_item.on("click", function(){
		last_item.before('<li><input type="text"></li>');
	});
    
    // upon clicking the "V" shaped icon, the list of attributes
    // will slide down and appear
    $(".list").on("click", "img", function()
    {
        $(this).next("ul").slideDown(500);
    });
    
    $(".list").on("click", "li", function()
    {
        $(this).next("ul").slideDown(500);
    });
    
    // upon the "title" li's losing focus, the list of attributes
    // will slide back up and hide
    $(".list").on("mouseleave", "img", function()
    {
        $(this).next("ul").slideUp(500);
    });
});
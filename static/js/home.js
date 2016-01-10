$(document).ready(function()
{
    // upon clicking the last li in the list, a new li will be 
    // formed right above it (so last li remains last)
    $(".list").on("click", ".addRow", function()
    {
        $(".addRow").before('<div class="attributes"><div class="attribute"><div class="key"><input type="text"></div><div class = "value"><input type="text"></div></div></div>');
    });

    // upon clicking the "V" shaped icon, the list of attributes
    // will slide down and appear
    $(".list").on("click", "img", function()
    {
        $(this).find("attribute").slideDown(500);
        $(this).find("attribute").attr("display","block");
    });

    // upon the "title" li's losing focus, the list of attributes
    // will slide back up and hide
    $(".list").on("blur", "listItem", function()
    {
        $(this).find("attribute").slideUp(500);
    });
});
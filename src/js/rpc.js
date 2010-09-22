
//adapted from http://code.google.com/appengine/articles/rpc.html

  
//  As mentioned at http://en.wikipedia.org/wiki/XMLHttpRequest
if( !window.XMLHttpRequest ) XMLHttpRequest = function()
{
    try{
        return new ActiveXObject("Msxml2.XMLHTTP.6.0")
    }catch(e){}
    try{
        return new ActiveXObject("Msxml2.XMLHTTP.3.0")
    }catch(e){}
    try{
        return new ActiveXObject("Msxml2.XMLHTTP")
    }catch(e){}
    try{
        return new ActiveXObject("Microsoft.XMLHTTP")
    }catch(e){}
    throw new Error("Could not find an XMLHttpRequest alternative.")
};

//
// Makes an AJAX request to a local server function w/ optional arguments
//
// functionName: the name of the server's AJAX function to call
// opt_argv: an Array of arguments for the AJAX function
//
function Request(function_name, opt_argv) {

    if (!opt_argv)
        opt_argv = new Array();

    // Find if the last arg is a callback function; save it
    var callback = null;
    var len = opt_argv.length;
    if (len > 0 && typeof opt_argv[len-1] == 'function') {
        callback = opt_argv[len-1];
        opt_argv.length--;
    }
    var async = (callback != null);

    // Encode the arguments in to a URI
    var query = 'action=' + encodeURIComponent(function_name);
    for (var i = 0; i < opt_argv.length; i++) {
        var key = 'arg' + i;
        var val = JSON.stringify(opt_argv[i]);
        query += '&' + key + '=' + encodeURIComponent(val);
    }
    query += '&time=' + new Date().getTime(); // IE cache workaround

    // Create an XMLHttpRequest 'GET' request w/ an optional callback handler
    var req = new XMLHttpRequest();
    req.open('GET', '/rpc?' + query, async);

    if (async) {
        req.onreadystatechange = function() {
            if(req.readyState == 4 && req.status == 200) {
                var response = null;
                try {
                    response = JSON.parse(req.responseText);
                } catch (e) {
                    response = req.responseText;
                }
                callback(response);
            }
        }
    }

    // Make the actual request
    req.send(null);
}


//my comments:
//Really, there isn't a way to wrap all the functions together in a secure closure?
//We have to try to allow functions by checking the function name?
//Anyway, couldn't a hacker just rewrite the function name and pass in malicious code?
//I don't get it...  trying to think of a better solution....


// Adds a stub function that will pass the arguments to the AJAX call
function InstallFunction(obj, functionName) {
    obj[functionName] = function() {
        Request(functionName, arguments);
    }
}


// Server object that will contain the callable methods
var server = {};

// Insert the samples as the name of a callable method
InstallFunction(server, 'Sample1');
InstallFunction(server, 'Sample2');

//my comments:
//really, this just pointlessly roundabout.  I'm clearly not understanding this - why can't we wrap all the functions together?
//I need to understand this security better before messing with it...



//
//-------------
// Client functions that call a server rpc and provide a callback
//these functions use jQuery and should be called from within a $(document).ready

function doSample1() {
    server.Sample1($('num1').value, $('num2').value, callback1);
}
function callback1(response) {
    $('result').value = response +  " numbers have been added"
}

function doSample2() {
    server.Sample2($('num1').value, $('num2').value, callback2);
}
function callback1(response) {
    $('result').value = response + " numbers have been multiplied";
}
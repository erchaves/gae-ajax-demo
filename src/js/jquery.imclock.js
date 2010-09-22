/*
 * jQuery imclock plugin with serwer time synchronization
 * Go to http://imlog.pl/2010/01/23/imclock-server-synchronized.html
 * for more info and docummentation.
 *
 * Copyright (c) 2010 Ignacy Moryc  <imoryc@gmail.com>
 * Licensed under the MIT License:
 *   http://www.opensource.org/licenses/mit-license.php
 */

(function($) {

   $.fn.imclock = function(options) {
     var settings = jQuery.extend({
                                    name: "defaultName",
                                    size: 5
                                  }, options);
     var version = '1.4.0';
     return $.fn.imclock.start($(this), null);
   };

   // TODO 2: sepparate time setting interval and clock starting
   $.fn.imclock.start = function(element, time) {
     if (time == null)
     {
       var time = $.fn.imclock.getServerTime(element);
     }
     else
     {
       time.setSeconds(time.getSeconds() + 1);
     }
     var hours = time.getHours();
     var minutes = time.getMinutes();
     var seconds = time.getSeconds();

     if (minutes<10) {
       minutes = '0' + minutes;
     }
     if (seconds<10) {
       seconds = '0' + seconds;
     }

     element.html(hours+ ":" + minutes + ":" + seconds);
     element.timerID = setTimeout(function(){$.fn.imclock.start(element, time);},1000);
   };

   // This is the function that gets the actual time from the server
   // time is expected to be returned as JSON data in field named "time"
   // For example the request could look like this:
   // {
   //  some_data: "lorem",
   //  time : 2010-12-12T12:23
   // }
   $.fn.imclock.getServerTime = function(element) {
     var time = null;
     if ($("#time_href").length) {
       var url = $("#time_href")[0].innerHTML;
       $.getJSON(url, function(data) {
                   if (data){
                   time = new Date(Date.parse(data.time));                     
                   }
                 });
     }
     if (time == null) {
       time = new Date();
     }
     return time;
   };

 })(jQuery);

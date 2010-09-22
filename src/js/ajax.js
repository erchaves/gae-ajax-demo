(function($){
//avoid colllisions with other plugins using $

    //$() is okay - will be called in a $(document).ready
    function updateNode($node, urlPath, cacheBool) {
        $.ajax({
            url: urlPath,
            cache: cacheBool,
            success: function(frag){
                $node.html(frag);
            }
        });
    };

    //using polling for now - Change this when google launches their Channel API (see http://www.youtube.com/watch?v=oMXe-xK0BWA, http://groups.google.com/group/google-appengine/browse_thread/thread/48d459f522d257d1?tvc=2)
    $(document).ready(function() {

        var updateNodes = function(){
            updateNode( $("#chatContent"), "/messages", false);
        };
        //do once at the start
        updateNodes();
        setInterval(updateNodes, 4000);
    });
})(jQuery);
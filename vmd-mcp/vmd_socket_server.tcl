# vmd_socket_server.tcl
#
# A Tcl socket server for VMD (Visual Molecular Dynamics)
# This script listens on a TCP port, executes incoming Tcl commands,
# and returns JSON responses to the connected MCP server client.
#
# To start the server in VMD:
#   source vmd_socket_server.tcl
# Or inside VMD's Tk Console:
#   play vmd_socket_server.tcl

set port 9877
set server_socket ""

proc vmd_socket_accept {channel client_addr client_port} {
    puts "VMD MCP Client connected from $client_addr:$client_port"
    fconfigure $channel -buffering line -blocking 0
    fileevent $channel readable [list vmd_socket_read $channel]
}

proc vmd_socket_read {channel} {
    if {[gets $channel line] < 0} {
        if {[eof $channel]} {
            puts "VMD MCP Client disconnected"
            catch {close $channel}
        }
    } else {
        set trimmed_line [string trim $line]
        if {$trimmed_line eq ""} {
            return
        }
        
        puts "Received VMD command: $trimmed_line"
        
        # Execute the command in the global namespace
        if {[catch {uplevel #0 $trimmed_line} result]} {
            # On error, format an error JSON response
            set escaped_msg [escape_json $result]
            set response "{\"status\": \"error\", \"message\": \"$escaped_msg\"}"
            puts "Command error: $result"
        } else {
            # On success, format a success JSON response
            set escaped_res [escape_json $result]
            set response "{\"status\": \"success\", \"result\": \"$escaped_res\"}"
            puts "Command result: $result"
        }
        
        # Send response back to the client
        if {[catch {puts $channel $response; flush $channel} err]} {
            puts "Error writing response to client: $err"
            catch {close $channel}
        }
    }
}

proc escape_json {str} {
    # Replace backslashes, quotes, and newlines for valid JSON
    regsub -all {\\} $str {\\\\} str
    regsub -all {"} $str {\\"} str
    regsub -all {\n} $str {\\n} str
    regsub -all {\r} $str {\\r} str
    regsub -all {\t} $str {\\t} str
    return $str
}

# Stop any existing server before starting a new one
if {$server_socket ne ""} {
    catch {close $server_socket}
}

if {[catch {socket -server vmd_socket_accept $port} server_socket]} {
    puts "Error: Could not start VMD MCP server on port $port: $server_socket"
} else {
    puts "=========================================================="
    puts " VMD MCP Socket Server started successfully!"
    puts " Listening on port: $port"
    puts " Keep VMD open and source this script in VMD to enable control."
    puts "=========================================================="
}

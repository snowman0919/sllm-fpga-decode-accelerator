package require ::quartus::flow

set script_dir [file dirname [file normalize [info script]]]
set project_dir [file normalize [file join $script_dir ..]]
set project_name de10_lite_uart_matvec
set revision_name de10_lite_uart_matvec

cd $project_dir
project_open $project_name -revision $revision_name
execute_flow -compile
project_close

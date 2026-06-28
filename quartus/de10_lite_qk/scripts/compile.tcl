package require ::quartus::project
package require ::quartus::flow

set script_dir [file dirname [file normalize [info script]]]
set project_dir [file normalize [file join $script_dir ..]]
set project_name de10_lite_qk
set project_file [file join $project_dir ${project_name}.qpf]

if {![file exists $project_file]} {
  post_message -type error "Quartus project file not found: $project_file"
  post_message -type error "Run 'just quartus-project' first."
  qexit -error
}

if {[catch {
  cd $project_dir
  project_open -revision $project_name $project_name
  execute_flow -compile
  project_close
} err]} {
  post_message -type error $err
  catch {project_close}
  qexit -error
}

post_message -type info "Quartus compile completed. Check output_files/ for reports and the .sof artifact."

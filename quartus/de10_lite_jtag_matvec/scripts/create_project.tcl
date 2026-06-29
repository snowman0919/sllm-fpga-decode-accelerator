package require ::quartus::project
package require ::quartus::flow

set script_dir [file dirname [file normalize [info script]]]
set project_dir [file normalize [file join $script_dir ..]]
set repo_root [file normalize [file join $project_dir .. ..]]
set project_name de10_lite_jtag_matvec
set revision_name de10_lite_jtag_matvec
set top_level De10LiteJtagMatVecTop
set device_name 10M50DAF484C7G
set board_top_file [file join $project_dir De10LiteJtagMatVecTop.v]
set generated_dir [file join $project_dir generated_verilog]
set platform_designer_dir [file join $project_dir platform_designer]
set qsys_file [file join $platform_designer_dir jtag_matvec_system.qsys]
set qip_file [file join $platform_designer_dir jtag_matvec_system synthesis jtag_matvec_system.qip]
set sdc_file [file join $project_dir de10_lite_jtag_matvec.sdc]
set verified_qsf [file join $project_dir qsf de10_lite_pins.qsf]
set qsf_path [file join $project_dir ${revision_name}.qsf]

set verilog_files [list $board_top_file]
set verilog_assignments [list "De10LiteJtagMatVecTop.v"]
set qip_assignment "platform_designer/jtag_matvec_system/synthesis/jtag_matvec_system.qip"
set sdc_assignment "de10_lite_jtag_matvec.sdc"
set ip_search_assignment "ip/qk_jtag_decode_matvec_reg_top"

set missing 0
foreach f [concat $verilog_files [list $qsys_file $qip_file $sdc_file]] {
  if {![file exists $f]} {
    post_message -type error "Required input missing: $f"
    set missing 1
  }
}
if {$missing} {
  qexit -error
}

cd $project_dir
project_new $project_name -overwrite -revision $revision_name
set_global_assignment -name FAMILY "MAX 10"
set_global_assignment -name DEVICE $device_name
set_global_assignment -name TOP_LEVEL_ENTITY $top_level
set_global_assignment -name PROJECT_OUTPUT_DIRECTORY output_files
set_global_assignment -name IP_SEARCH_PATHS $ip_search_assignment

foreach vf $verilog_assignments {
  set_global_assignment -name VERILOG_FILE $vf
}
set_global_assignment -name QIP_FILE $qip_assignment
set_global_assignment -name SDC_FILE $sdc_assignment

export_assignments
project_close

if {[file exists $verified_qsf]} {
  post_message -type info "Including verified DE10-Lite QSF: $verified_qsf"
  set handle [open $qsf_path a]
  puts $handle ""
  puts $handle "# Verified DE10-Lite pin assignments"
  puts $handle "source qsf/de10_lite_pins.qsf"
  close $handle
} else {
  post_message -type warning "Verified DE10-Lite QSF not found: $verified_qsf"
}

post_message -type info "Created Quartus JTAG MatVec project under $project_dir"

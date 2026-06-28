set script_dir [file dirname [file normalize [info script]]]
set project_dir [file normalize [file join $script_dir ..]]
set sof_file [file join $project_dir output_files de10_lite_qk.sof]
set cable_name "USB-Blaster"
if {[info exists ::env(QUARTUS_CABLE)] && $::env(QUARTUS_CABLE) ne ""} {
  set cable_name $::env(QUARTUS_CABLE)
}

proc parse_cable_lines {cable_output} {
  set cables {}
  foreach line [split $cable_output "\n"] {
    if {[regexp {^\s*\d+\)\s+(.+?)\s*$} $line -> cable]} {
      lappend cables $cable
    }
  }
  return $cables
}

proc resolve_cable_name {requested_name cable_output} {
  set exact_match ""
  set partial_matches {}

  foreach cable [parse_cable_lines $cable_output] {
    if {$cable eq $requested_name} {
      set exact_match $cable
      break
    }
    if {[string first $requested_name $cable] >= 0} {
      lappend partial_matches $cable
    }
  }

  if {$exact_match ne ""} {
    return $exact_match
  }
  if {[llength $partial_matches] == 1} {
    return [lindex $partial_matches 0]
  }
  if {[llength $partial_matches] > 1} {
    puts stderr "Requested cable '$requested_name' matched multiple hardware cables."
    puts stderr "Set QUARTUS_CABLE to one exact cable name from 'quartus_pgm -l':"
    foreach cable $partial_matches {
      puts stderr "  $cable"
    }
    exit 1
  }

  return ""
}

if {![file exists $sof_file]} {
  puts stderr "Programming file not found: $sof_file"
  puts stderr "Run Quartus compile first."
  exit 1
}

if {[catch {exec quartus_pgm -l} cable_output]} {
  puts stderr "quartus_pgm is unavailable or failed to enumerate hardware."
  puts stderr $cable_output
  exit 1
}

set resolved_cable_name [resolve_cable_name $cable_name $cable_output]
if {$resolved_cable_name eq ""} {
  puts stderr "Requested cable '$cable_name' was not found."
  puts stderr "quartus_pgm -l output:"
  puts stderr $cable_output
  exit 1
}

puts "Using Quartus cable '$resolved_cable_name'."

if {[catch {exec quartus_pgm -m jtag -c $resolved_cable_name -o p\;$sof_file} program_output]} {
  puts stderr "quartus_pgm failed while trying to program $sof_file"
  puts stderr $program_output
  exit 1
}

puts $program_output
puts "Programming attempt completed for $sof_file via cable '$resolved_cable_name'."

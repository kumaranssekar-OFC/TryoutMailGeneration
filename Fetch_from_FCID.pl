#################################################################################################################
#!perl.exe
#
# FILE:   Fetch_from_FCID.pl
# 
# Status : REVIEW (AFR)
#
# DESCRIPTION:  Fetch Board Id and GNSS info from FCID sheet and displays it. 
#
# USAGE:        see help_text
#
# PREREQUISITE: FCID Table has to be found in same directory as this script
#
# HISTORY:
#
# Date            	| Author          				| Modification
#19-Aug-2024   		| Suriya Thangavel       		| Initial version to fetch Board-ID and GNSS
#
#####################################################################################################################################################################################################

my $lib;
BEGIN {
  use File::Basename;
  $lib = dirname($0);
}

use strict;
use warnings;
use 5.010;
use cc42;
use Win32::OLE qw(in with);
use Win32::OLE::Const 'Microsoft Excel';
use Data::Dumper;
use Getopt::Long;
use Cwd;
use List::MoreUtils qw(uniq);


my $debug = "";
my $error_string = "";
my $help_text = "";
my $base_dir        = dirname($0);
my $log_file        = "$base_dir\\Fetch_FCID_log.log";
my $cur_dir         = getcwd();
   $cur_dir         =~ s/\//\\/g;
my $xl_fcidtable = "";
my $findpn = "";
my %pndetails_hash;

# Excel vars
my $E_file       = "";
my $E_excel      = "";
my $E_workbook_fcid   = "";
my $E_worksheet_fcid  = "";

my $h_fcid = "SW_Variant_ID /
FCID (HEX)";
my $h_boardid = "Board ID/DTB"	;
my $h_emmc1 = "Partitioning Schema 1
(1st eMMC)"	;
my $h_adr = "ADR_FW_Type";
my $h_navigation = "Navigation";
my $h_sxm = "SXM";
my $h_teseo = "GNSS";
my $h_fpga = "FPGA (Sub-PCB)
CPLD (Fascia)";
my $h_cpld = "CPLD
(PORT EXTENDER)";
my $h_customer = "Customer
(fixed by RFS)";
my $h_bosch_pn = "Bosch Partnumber (HW-Index)";
my $h_group_info = "Grouping (only naming)";
my $h_rfs_type = "RFS
(as in Manifest)";

my $board_id = "";
my $gnss = "";
my $sxm_ver = "";
# Usage
$help_text = "
Usage:
   perl $0 -h|-fcid <FCID_sheet> -p <partnumber>

    -h                     			: Print this usage text.
    -fcid <FCID_sheet>     			: FCID sheet (SWUPD_Tooling_VXXX.xlsx)
	-p <partnumber>         		: partnumber to find sister device
\n";


#############################################################
#			Start of the script
#############################################################

scan_args(); # Scan whether all the mandatory parameters are provided.

E_Start();

parse_fcidtable();

#####################################################################################################################################################################################################

sub parse_fcidtable {

my @header_arr;
my @my_pn_details;


	$E_workbook_fcid  = $E_excel->Workbooks->Open("$xl_fcidtable") or die "Unable to open workbook $xl_fcidtable\n";
	$E_worksheet_fcid = $E_workbook_fcid->WorkSheets("Variants");
	$E_worksheet_fcid ->Activate(); 
	
	
	#$E_workbook_hwlist  = $E_excel->Workbooks->Open("$xl_hwlist") or die "Unable to open workbook $xl_hwlist\n";
	
	
	######## Find Partnumber Details from FCID Table #######
	my ($_header_row,$_header_PN_col) = Search_text_in_excel($E_worksheet_fcid,0,$h_bosch_pn,"-","-");
	
	for (my $i = 1 ; $i <= $E_worksheet_fcid->UsedRange->Columns->{'Count'} ; $i++) {
		next unless defined $E_worksheet_fcid->Cells($_header_row,$i)->{'Value'};
		$header_arr[$i] = $E_worksheet_fcid->Cells($_header_row,$i)->{'Value'};
	}
	
	print @header_arr if $debug;
	
	my ($_my_pn_row,$_my_pn_col) = Search_text_in_excel($E_worksheet_fcid,1,$findpn,"-",$_header_PN_col);
	
	print "Partnumber found at $_my_pn_row,$_my_pn_col" if $debug;
	
	if ($_my_pn_row == 0 && $_my_pn_col == 0) {
		print "\n";
		print "  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"; 
		print "  !! Unable to find the specified part number in the FCID sheet. Please check with different version !!\n";
		print "  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"; 
		exit 1; 
	}
	
	for (my $i = 1 ; $i <= $E_worksheet_fcid->UsedRange->Columns->{'Count'} ; $i++) {
		next unless defined $E_worksheet_fcid->Cells($_my_pn_row,$i)->{'Value'};
		$my_pn_details[$i] = $E_worksheet_fcid->Cells($_my_pn_row,$i)->{'Value'};
		$my_pn_details[$i] =~ s/\n//g; 
		print $E_worksheet_fcid->Cells($_my_pn_row,$i)->{'Value'} if $debug;
	}
	
	for (my $i = 1 ; $i <= $#header_arr; $i++) {
		$pndetails_hash{$findpn}{$header_arr[$i]} = $my_pn_details[$i] ; 
		#print "\n\n$header_arr[$i] \t\t -->  $my_pn_details[$i]";
	}
	print Dumper \%pndetails_hash if $debug;
	
	print "\n################ Given PN \"$findpn\" has following details ################\n"; 
	print "\tBoard id\t\t---------> $pndetails_hash{$findpn}{$h_boardid}\n"; 
	print "\tFCID\t\t\t---------> $pndetails_hash{$findpn}{$h_fcid}\n"; 
	print "\tPartition (emmc1)\t---------> $pndetails_hash{$findpn}{$h_emmc1}\n"; 
	print "\tADR\t\t\t---------> $pndetails_hash{$findpn}{$h_adr}\n"; 
	print "\tNavigation\t\t---------> $pndetails_hash{$findpn}{$h_navigation}\n"; 
	print "\tSXM\t\t\t---------> $pndetails_hash{$findpn}{$h_sxm}\n";
	print "\tTESEO\t\t\t---------> $pndetails_hash{$findpn}{$h_teseo}\n";
	print "\tFPGA\t\t\t---------> $pndetails_hash{$findpn}{$h_fpga}\n";
	print "\tCPLD\t\t\t---------> $pndetails_hash{$findpn}{$h_cpld}\n";
	print "\tCustomer\t\t---------> $pndetails_hash{$findpn}{$h_customer}\n";
	print "\tRFS\t---------> $pndetails_hash{$findpn}{$h_rfs_type}\n";
	print "\tGrouping\t---------> $pndetails_hash{$findpn}{$h_group_info}\n";
	print "\tBosch Part Numbers\t---------> $pndetails_hash{$findpn}{$h_bosch_pn}\n";
	
	
	$board_id = $pndetails_hash{$findpn}{$h_boardid};
	$gnss = $pndetails_hash{$findpn}{$h_teseo};
	$sxm_ver = $pndetails_hash{$findpn}{$h_sxm};
	 
	print "\n Board_ID = $board_id";
	print "\n GNSS = $gnss";
	print "\n SXM = $sxm_ver";
	# print "\n group_info = $group_info";
	
	
	end: E_Close($E_worksheet_fcid,$xl_fcidtable);
	
}
#####################################################################################################################################################################################################
sub Search_text_in_excel {
 my $wrk_sheet = $_[0] || "";
 my $fullmatch = $_[1] || 0;
 my $srch_string = $_[2] || "";
  my $rows = $_[3]||1;
 my $cols = $_[4]||1;
 my $row_max ;
 my $col_max;
my $int_row;
my $int_col;

	print "\nSearch for $srch_string in ".$wrk_sheet->Name."\n" if $debug;
	
	if ($rows =~ /-/) {
		($int_row,$row_max) = split('-',$rows);
		if ($int_row eq "") { $int_row = 1; }
		if ($row_max eq "") { $row_max = $wrk_sheet->UsedRange->Rows->{'Count'}; }
	} else {
		$int_row = $rows;
		$row_max = $rows;
	}
	
	if ($cols =~ /-/) {
		($int_col,$col_max) = split('-',$cols);
		if ($int_col eq "") { $int_col = 1; }
		if ($col_max eq "") { $col_max = $wrk_sheet->UsedRange->Columns->{'Count'}; }
	} else {
		$int_col = $cols;
		$col_max = $cols;
	}
	
	print "Search starts at Row $int_row - $row_max \nSearch starts at Column $int_col - $col_max\n" if $debug;
		
	for my $row ( $int_row .. $row_max+1 ) {
		for my $col ( $int_col .. $col_max+1 ) {
		print "\nSearch for $srch_string in ".$wrk_sheet->Name." \,Value read -- Row : $row \, Col : $col" if $debug;
		#write_log("\nSearch for $srch_string in ".$wrk_sheet->Name." \,Value read -- Row : $row \, Col : $col","INFO");
		#Return the cell object at $row and $col
			next unless defined $wrk_sheet->Cells($row,$col)->{'Value'};
			my $cell = $wrk_sheet->Cells($row,$col)->{'Value'};
			next unless $cell;
			$cell =~ s/\s+\n/ /g;
			chomp($cell);
			#print "\n  Cell value = $cell\n";
			my @PNs = split(',|\n',$cell);
			
			#print "\n @PNs";
			
			foreach my $pn (@PNs) {
				#print "\nPN -  $pn";
				$pn =~ s/\s+\n/ /g;
				chomp($pn);
				#print "\n-->$pn";
				if ( $fullmatch == 0 && index($pn, $srch_string) != -1) {
					print "\n\nSearch_text_in_excel returns --> (row,col) \= ($row,$col) \n" if $debug;
					return ($row,$col);
				}
				elsif ( $fullmatch == 1 && $pn eq $srch_string ) {
					print "\n\nSearch_text_in_excel returns --> (row,col) \= ($row,$col) \n" if $debug;
					return ($row,$col);
				}
			}
		}
	}
	print "\n$srch_string is not found!!!" if $debug;
	return (0,0); ## Return (0,0) incase of string not found in the sheet.
}

#####################################################################################################################################################################################################
sub E_Start { 
# Open Excel application
$E_excel = (Win32::OLE->new("Excel.Application", 'Quit'))
             or die( "Could not start \"Excel.Application\"" );
  $E_excel->{DisplayAlerts}=0;
}
#####################################################################################################################################################################################################  
sub E_Close {
  # close excel sheet
  my $E_handle = shift;
  my $E_file = shift;
  $E_handle->Saveas($E_file);
  $E_handle->Close;
}
#####################################################################################################################################################################################################
sub scan_args {

	local * check_file = sub
	{
		my $file = shift;
		
		if (-e $cur_dir."\\".$file) {
		  $file = $cur_dir."\\".$file;
		}
		elsif (-e $base_dir."\\".$file) {
		  $file = $base_dir."\\".$file;
		}
		elsif (-e $file) { # nothing to be done, setting ok
		}
		else {
		  $error_string .= "$file not found!\n";
		  exit_script(1);
		}
		return $file;
	};

	my $h         = "";
	  
	my $res = GetOptions (
		'h'        => \$h,
		'fcid=s'   => \$xl_fcidtable,
		'p=s'		 => \$findpn,
		
	) or die("$help_text");
	  
		if ($h) {
		print $help_text;
		exit(0);
	}
	  
	if ($xl_fcidtable) {
		$xl_fcidtable = check_file($xl_fcidtable);
		chomp($xl_fcidtable);
	}
	else {
		print ("FCID Excel input file is missing\n");
	}
  
}
#####################################################################################################################################################################################################
sub exit_script
{
  my $exit_code = shift;
  if ($exit_code ne "0" || $error_string ne "") { # exit with error_string
   $exit_code = 2 if ($exit_code eq "0");
   cc42::print_banner_error("$error_string");
   #write_log("$error_string","ERROR_LIST");
  }
  #write_log("Done... (Exit with $exit_code)\n","INFO");
  print("\nLog written to $log_file\n");
  print("Done... (Exit with $exit_code)\n");
  exit($exit_code);
}
######################################################################################################################################################################################################
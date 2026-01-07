#################################################################################################################
#!perl.exe
#
# FILE:   tryout_devices.pl
# 
# Status : REVIEW (AFR)
#
# DESCRIPTION:  searches the appropriate Tryout devices from HW list excel dump from JIRA and displays it. 
#
# USAGE:        see help_text
#
# PREREQUISITE: cc42.pm , HW list dump from JIRA , FCID Table has to be found in same directory as this script
#
# HISTORY:
#
# Date            	| Author          				| Modification
#11-Nov-2019   		| Dinesh Kumar Saravanan  		| Initial version
#24-May-2023   		| Suriya Thangavel				| Additional condition added to find devices without customer info
#02-August-2024   	| Suriya Thangavel				| Script is modified to select the sister device sheet based on input partnumber
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
my $log_file        = "$base_dir\\tryout_devices_log.txt";
my $cur_dir         = getcwd();
   $cur_dir         =~ s/\//\\/g;
my $xl_fcidtable = "";
#my $xl_hwlist = "Tryout_devices\@Cob.xlsx";
my $xl_hwlist = "";
my $findpn = "";
my %pndetails_hash;
my $HW_Key_header_col; 
my $variant ="";
my $variant_customer = "";
my $group_info = "";
my $adr_info = "";

# Excel vars
my $E_file       = "";
my $E_excel      = "";
my $E_workbook_fcid   = "";
my $E_worksheet_fcid  = "";
my $E_workbook_hwlist = "";
my $E_worksheet_hwlist  = "";
my $sheet_name = "";
my $E_workbook = "";
my $E_worksheet = "";

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

# Usage
$help_text = "
Usage:
   perl $0 -h|-fcid <FCID_sheet> -hwlist <sister_device_excel> -p <partnumber>

    -h                     			: Print this usage text.
    -fcid <FCID_sheet>     			: FCID sheet (SWUPD_Tooling_VXXX.xlsx)
	-hwlist <sister_device_excel>   : Sister device list excel (Tryout_devices_XXXX.xlsx)
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
	
	
	$E_workbook_hwlist  = $E_excel->Workbooks->Open("$xl_hwlist") or die "Unable to open workbook $xl_hwlist\n";
	
	
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
	
	$adr_info = lc($pndetails_hash{$findpn}{$h_adr}); 
	$variant = lc($pndetails_hash{$findpn}{$h_rfs_type});
	$variant_customer = lc($pndetails_hash{$findpn}{$h_customer});
	$group_info = lc($pndetails_hash{$findpn}{$h_group_info});
	
	# print "\n variant = $variant";
	# print "\n variant_customer = $variant_customer";
	# print "\n group_info = $group_info";
	
	##Define the sheet name based on input partnumber
	if($variant =~ /rnaivi/)
	{
		if ($group_info =~ /mitsubishi/)
		{
			
			$sheet_name = "MMC";
			chomp($sheet_name);
		}
		elsif ($group_info =~ /gen4/)
		{
			$sheet_name = "A_P-IVI2_MMC";
			chomp($sheet_name);
		}
		else
		{
			$sheet_name = "N2N21N31";	
			chomp($sheet_name);
		}
	}
	elsif($variant =~ /rivie/)
	{
		if($group_info =~ /gen4/)
		{
			$sheet_name = "CCS1.1";
			chomp($sheet_name);
		}
		else
		{
			$sheet_name = "Reno";
			chomp($sheet_name);
		}
	}
	elsif($variant =~ /npivi/)
	{
		if($group_info =~ /gen4/)
		{
			$sheet_name = "A_P-IVI2_MMC";
			chomp($sheet_name);
		}
		else
		{
			$sheet_name = "PIVI";
			chomp($sheet_name);
		}
	}
	elsif($variant =~ /mmcivi2/)
	{
		$sheet_name = "A_P-IVI2_MMC";
		chomp($sheet_name);
	}
	print "\n\tSheet Selected = $sheet_name \n";	
		
	my @pn_arr = split(',',$pndetails_hash{$findpn}{$h_bosch_pn});
			
	### Level 1 device filtering ######		
	if (L1_check_pn_availablility (@pn_arr) != 0) {
		goto end;
	} ### Level 2 device filtering ### 
	elsif ( L2_check_pn_availablility () != 0) {
	#if ( L2_check_pn_availablility () != 0) {
		goto end;
	} ### Level 3 device filtering ### 
	elsif ( L3_check_pn_availablility() != 0 ) {
		goto end;
	}### Level 4 device filtering ### 
	elsif ( L4_check_pn_availablility() != 0 ) {
		goto end;
	}### Level 5 device filtering ### 
	elsif (L5_check_pn_availablility() != 0) {
		goto end;
	}### Level 6 device filtering ### 
	elsif (L6_check_pn_availablility() != 0) {
		goto end;
	}### Level 7 device filtering ### 
	elsif (L7_check_pn_availablility() != 0) {
		goto end;
	}### Level 8 device filtering ### 
	elsif (L8_check_pn_availablility() != 0) {
		goto end;
	}### Level 9 device filtering ### 
	elsif (L9_check_pn_availablility() != 0) {
		goto end;
	}### Level 10 device filtering ###
	elsif ( L10_check_pn_availablility() != 0 ) {
		goto end;
	}### Level 11 device filtering ### 
	elsif ( L11_check_pn_availablility() != 0 ) {
		goto end;
	}### Level 12 device filtering ### 
	elsif (L12_check_pn_availablility() != 0) {
		goto end;
	}
	else {
		print "\n";	
		print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"; 
		print "!! Unable to find the Tryout device. please try to find manually.!!\n";
		print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n";
	}
		
	end: E_Close($E_worksheet_fcid,$xl_fcidtable);
	
}

#####################################################################################################################################################################################################
sub L1_check_pn_availablility {

	my @pn_arr = @_;
	
	my $total_devices = 0; 
	#@pn_arr = split(',',@pn_arr);
	
	print "\n~~~~~~~ Finding Tryout devices - Level 1 search (with same device spec)~~~~~~~\n";
	return OL_check_pn_availablility ($pndetails_hash{$findpn}{$h_emmc1},$pndetails_hash{$findpn}{$h_boardid},$pndetails_hash{$findpn}{$h_adr},
										$pndetails_hash{$findpn}{$h_sxm},$pndetails_hash{$findpn}{$h_teseo},$pndetails_hash{$findpn}{$h_fpga},$pndetails_hash{$findpn}{$h_cpld},@pn_arr);
	
}
#####################################################################################################################################################################################################
## -> L2_check_pn_availablility - considers all the device specification and finds on other FCID table rows.  
sub L2_check_pn_availablility {

	print "\n~~~~~~~ Finding Tryout devices - Level 2 search with same emmc,Board id,ADR,SXM,GNSS,FPGA ~~~~~~~\n";
	return OL_check_pn_availablility ($pndetails_hash{$findpn}{$h_emmc1},$pndetails_hash{$findpn}{$h_boardid},$pndetails_hash{$findpn}{$h_adr},
										$pndetails_hash{$findpn}{$h_sxm},$pndetails_hash{$findpn}{$h_teseo},$pndetails_hash{$findpn}{$h_fpga},$pndetails_hash{$findpn}{$h_cpld});
	
	
}
#####################################################################################################################################################################################################
## -> L3_check_pn_availablility - doesnot consider Board-id 
sub L3_check_pn_availablility {
	
	print "\n~~~~~~~ Finding Tryout devices - Level 3 search with same emmc,ADR,SXM,GNSS,FPGA , but can be different board-id ~~~~~~~\n";
	return OL_check_pn_availablility ($pndetails_hash{$findpn}{$h_emmc1},"-",$pndetails_hash{$findpn}{$h_adr},
										$pndetails_hash{$findpn}{$h_sxm},$pndetails_hash{$findpn}{$h_teseo},$pndetails_hash{$findpn}{$h_fpga},$pndetails_hash{$findpn}{$h_cpld});
}
#####################################################################################################################################################################################################
## -> L3_check_pn_availablility - doesnot consider Board-id , if ADR is FM then consider all other adr's
sub L4_check_pn_availablility {
	
	my $adr = ""; 
	
	print "\n~~~~~~~ Finding Tryout devices - Level 4 search with same emmc,SXM,GNSS,FPGA, but can be different board-id , ADR ~~~~~~~\n";
	$adr = $pndetails_hash{$findpn}{$h_adr};
	## To avoid the adr in device filtering basic adr is used. 
	if ($adr eq 'AARS_IVI_S2_AC_FM') {

		$adr = "-"; 
	}

	
	
	return OL_check_pn_availablility ($pndetails_hash{$findpn}{$h_emmc1},"-",$adr,
										$pndetails_hash{$findpn}{$h_sxm},$pndetails_hash{$findpn}{$h_teseo},$pndetails_hash{$findpn}{$h_fpga},$pndetails_hash{$findpn}{$h_cpld});
}
#####################################################################################################################################################################################################
## -> L5_check_pn_availablility - doesnot consider Board-id , if ADR is FM then consider all other adr's, if CPLD/FPGA is not updatable then donot consider it. 
sub L5_check_pn_availablility {
	
	my $adr = ""; 
	my $GNSS = "";
	my $fpga = "";
	my $cpld = "";
	my $sxm = "";
	
	print "\n~~~~~~~ Finding Tryout devices - Level 5 search with same emmc, but with different board-id,ADR,SXM,GNSS,FPGA,CPLD ~~~~~~~\n";
	
	$GNSS = $pndetails_hash{$findpn}{$h_teseo};
	if ( $GNSS eq 'Teseo_not_updatable') {
		$GNSS = "-";
	}
	
	$fpga = $pndetails_hash{$findpn}{$h_fpga};
	$cpld = $pndetails_hash{$findpn}{$h_cpld};
	if ($fpga eq 'FPGA_and_CPLD_not_updatable') {
		$fpga = "-";
		$cpld = "-"
	}
	
	$sxm = $pndetails_hash{$findpn}{$h_sxm};
	if ($sxm eq 'SXM_not_updatable') {
		$sxm = "-";
	}
	
	$adr = $pndetails_hash{$findpn}{$h_adr};
	## To avoid the adr in device filtering basic adr is used. 
	if ($adr eq 'AARS_IVI_S2_AC_FM') {

		$adr = "-"; 
	}

	
	
	return OL_check_pn_availablility ($pndetails_hash{$findpn}{$h_emmc1},"-",$adr,$sxm,$GNSS,$fpga,$cpld);
}
#####################################################################################################################################################################################################
### Future upgradation!! ###
## -> L6_check_pn_availablility - search with different emmc, but same board-id,ADR,SXM,GNSS,FPGA,CPLD
sub L6_check_pn_availablility {
	
	my @all_partition_schema = ("PARTITION_SCHEMA8_NissanScope1","PARTITION_SCHEMA16__Nav","PARTITION_SCHEMA32__NavSmallSdb","PARTITION_SCHEMA32__NavLargeSdb","PARTITION_SCHEMA8__DASdb","PARTITION_SCHEMA64__NavRenault","PARTITION_SCHEMA64__ST2X_NavRenault",
								"PARTITION_SCHEMA16__ST2X_NavRenault","PARTITION_SCHEMA8__ST2X_DARenaultObigo","PARTITION_SCHEMA32__ST2X_NavRenaultObigo","PARTITION_SCHEMA32__ST2X_NavRenaultNarObigo","PARTITION_SCHEMA128__NavPiviJpn","PARTITION_SCHEMA64__ST3X_NavRenault",
								"PARTITION_SCHEMA32__DA","PARTITION_SCHEMA32__ROW_HIGHRES","PARTITION_SCHEMA32__ST3X_DA","PARTITION_SCHEMA8__ST3X_DARenaultObigo","PARTITION_SCHEMA32__ST3X_NavRenaultNarObigo","PARTITION_SCHEMA32__ST3X_NavRenaultObigo","PARTITION_SCHEMA16__DA",
								"PARTITION_SCHEMA8__DARenaultObigo" );
	my $emmc = "";
	
	print "\n~~~~~~~ Finding Tryout devices - Level 6 search with different emmc, but same board-id,ADR,SXM,GNSS,FPGA,CPLD ~~~~~~~\n";
	
	$emmc = $pndetails_hash{$findpn}{$h_emmc1};
	
	my ($partition_size,$format) = split('__',$emmc);
	
	#print "\n $partition_size \n";
	
	foreach my $schema (@all_partition_schema) {
		my $devicesfound = 0;
		if ( index($schema,$partition_size) != -1) {
			#print "\n$schema";	
			$devicesfound = OL_check_pn_availablility ($schema,"-",$pndetails_hash{$findpn}{$h_adr},$pndetails_hash{$findpn}{$h_sxm},$pndetails_hash{$findpn}{$h_teseo},$pndetails_hash{$findpn}{$h_fpga},$pndetails_hash{$findpn}{$h_cpld});
		}
		if ($devicesfound != 0) {
			return $devicesfound;
		}
		
		
	}
	
	return 0; ## devices not found.
	
}
#####################################################################################################################################################################################################
## -> L7_check_pn_availablility - Different Partition scheme, board-id , ADR , SXM , GNSS , FPGA , CPLD
sub L7_check_pn_availablility {
	
	my @all_partition_schema = ("PARTITION_SCHEMA8_NissanScope1","PARTITION_SCHEMA16__Nav","PARTITION_SCHEMA32__NavSmallSdb","PARTITION_SCHEMA32__NavLargeSdb","PARTITION_SCHEMA8__DASdb","PARTITION_SCHEMA64__NavRenault","PARTITION_SCHEMA64__ST2X_NavRenault",
								"PARTITION_SCHEMA16__ST2X_NavRenault","PARTITION_SCHEMA8__ST2X_DARenaultObigo","PARTITION_SCHEMA32__ST2X_NavRenaultObigo","PARTITION_SCHEMA32__ST2X_NavRenaultNarObigo","PARTITION_SCHEMA128__NavPiviJpn","PARTITION_SCHEMA64__ST3X_NavRenault",
								"PARTITION_SCHEMA32__DA","PARTITION_SCHEMA32__ROW_HIGHRES","PARTITION_SCHEMA32__ST3X_DA","PARTITION_SCHEMA8__ST3X_DARenaultObigo","PARTITION_SCHEMA32__ST3X_NavRenaultNarObigo","PARTITION_SCHEMA32__ST3X_NavRenaultObigo","PARTITION_SCHEMA16__DA",
								"PARTITION_SCHEMA8__DARenaultObigo" );

	my $emmc = "";
	
	print "\n~~~~~~~ Finding Tryout devices - Level 7 search with different Partition scheme, board-id , ADR , SXM , GNSS , FPGA , CPLD ~~~~~~~\n";
	
	$emmc = $pndetails_hash{$findpn}{$h_emmc1};


    my $adr = ""; 
	my $GNSS = "";
	my $fpga = "";
	my $cpld = "";
	my $sxm = "";
	
	$GNSS = $pndetails_hash{$findpn}{$h_teseo};
	if ( $GNSS eq 'Teseo_not_updatable') {
		$GNSS = "-";
	}
	
	$fpga = $pndetails_hash{$findpn}{$h_fpga};
	$cpld = $pndetails_hash{$findpn}{$h_cpld};
	if ($fpga eq 'FPGA_and_CPLD_not_updatable') {
		$fpga = "-";
		$cpld = "-"
	}
	
	$sxm = $pndetails_hash{$findpn}{$h_sxm};
	if ($sxm eq 'SXM_not_updatable') {
		$sxm = "-";
	}
	
	$adr = $pndetails_hash{$findpn}{$h_adr};
	## To avoid the adr in device filtering basic adr is used. 
	if ($adr eq 'AARS_IVI_S2_AC_FM') {

		$adr = "-"; 
	}

	my ($partition_size,$format) = split('__',$emmc);
	
	#print "\n $partition_size \n";
	
	foreach my $schema (@all_partition_schema) {
		my $devicesfound = 0;
		if ( index($schema,$partition_size) != -1) {
			print "\n$schema";	
			$devicesfound = OL_check_pn_availablility ($schema,"-",$adr,$sxm,$GNSS,$fpga,$cpld);
		}
		if ($devicesfound != 0) {
			return $devicesfound;
		}
		
		
	}
	
	return 0; ## devices not found.

}
#####################################################################################################################################################################################################
## -> L8_check_pn_availablility - Different Partition scheme and size, board-id , ADR , SXM , GNSS , FPGA , CPLD
sub L8_check_pn_availablility {
	
	my @all_partition_schema = ("PARTITION_SCHEMA8_NissanScope1","PARTITION_SCHEMA16__Nav","PARTITION_SCHEMA32__NavSmallSdb","PARTITION_SCHEMA32__NavLargeSdb","PARTITION_SCHEMA8__DASdb","PARTITION_SCHEMA64__NavRenault","PARTITION_SCHEMA64__ST2X_NavRenault",
								"PARTITION_SCHEMA16__ST2X_NavRenault","PARTITION_SCHEMA8__ST2X_DARenaultObigo","PARTITION_SCHEMA32__ST2X_NavRenaultObigo","PARTITION_SCHEMA32__ST2X_NavRenaultNarObigo","PARTITION_SCHEMA128__NavPiviJpn","PARTITION_SCHEMA64__ST3X_NavRenault",
								"PARTITION_SCHEMA32__DA","PARTITION_SCHEMA32__ROW_HIGHRES","PARTITION_SCHEMA32__ST3X_DA","PARTITION_SCHEMA8__ST3X_DARenaultObigo","PARTITION_SCHEMA32__ST3X_NavRenaultNarObigo","PARTITION_SCHEMA32__ST3X_NavRenaultObigo","PARTITION_SCHEMA16__DA",
								"PARTITION_SCHEMA8__DARenaultObigo" );

	my $emmc = "";
	
	print "\n~~~~~~~ Finding Tryout devices - Level 8 search with different Partition scheme and size, board-id , ADR , SXM , GNSS , FPGA , CPLD ~~~~~~~\n";
	
	$emmc = $pndetails_hash{$findpn}{$h_emmc1};


    my $adr = ""; 
	my $GNSS = "";
	my $fpga = "";
	my $cpld = "";
	my $sxm = "";
	
	$GNSS = $pndetails_hash{$findpn}{$h_teseo};
	if ( $GNSS eq 'Teseo_not_updatable') {
		$GNSS = "-";
	}
	
	$fpga = $pndetails_hash{$findpn}{$h_fpga};
	$cpld = $pndetails_hash{$findpn}{$h_cpld};
	if ($fpga eq 'FPGA_and_CPLD_not_updatable') {
		$fpga = "-";
		$cpld = "-"
	}
	
	$sxm = $pndetails_hash{$findpn}{$h_sxm};
	if ($sxm eq 'SXM_not_updatable') {
		$sxm = "-";
	}
	
	$adr = $pndetails_hash{$findpn}{$h_adr};
	## To avoid the adr in device filtering basic adr is used. 
	if ($adr eq 'AARS_IVI_S2_AC_FM') {

		$adr = "-"; 
	}

	my ($partition_size,$format) = split('__',$emmc);
	my ($targetdevicesize) = ($partition_size =~ /(\d+)$/);
	#print "\n $partition_size \n";
	
	foreach my $schema (@all_partition_schema) {
		my $devicesfound = 0;
		my ($C_device_partition_size,$format) = split('__',$schema);
		my ($C_device_size) = ($C_device_partition_size =~ /(\d+)$/);
		
		if ( $C_device_size >=  $targetdevicesize) {
			print "\n$schema";	
			$devicesfound = OL_check_pn_availablility ($schema,"-",$adr,$sxm,$GNSS,$fpga,$cpld);
		}
		if ($devicesfound != 0) {
			return $devicesfound;
		}
		
		
	}
	
	return 0; ## devices not found.

}
#####################################################################################################################################################################################################
## -> L9_check_pn_availablility - considers all the device specification except customer and finds on other FCID table rows.  
sub L9_check_pn_availablility {

	print "\n~~~~~~~ Finding Tryout devices - Level 9 search with same emmc,Board id,ADR,SXM,GNSS,FPGA  but different customer ~~~~~~~\n";
	return OC_check_pn_availablility ($pndetails_hash{$findpn}{$h_emmc1},$pndetails_hash{$findpn}{$h_boardid},$pndetails_hash{$findpn}{$h_adr},
										$pndetails_hash{$findpn}{$h_sxm},$pndetails_hash{$findpn}{$h_teseo},$pndetails_hash{$findpn}{$h_fpga},$pndetails_hash{$findpn}{$h_cpld});
	
	
}
#####################################################################################################################################################################################################
## -> L10_check_pn_availablility - doesnot consider Board-id & customer
sub L10_check_pn_availablility {
	
	print "\n~~~~~~~ Finding Tryout devices - Level 10 search with same emmc,ADR,SXM,GNSS,FPGA , but can be different board-id & customer ~~~~~~~\n";
	return OC_check_pn_availablility ($pndetails_hash{$findpn}{$h_emmc1},"-",$pndetails_hash{$findpn}{$h_adr},
										$pndetails_hash{$findpn}{$h_sxm},$pndetails_hash{$findpn}{$h_teseo},$pndetails_hash{$findpn}{$h_fpga},$pndetails_hash{$findpn}{$h_cpld});
}
#####################################################################################################################################################################################################
## -> L11_check_pn_availablility - doesnot consider Board-id, customer , if ADR is FM then consider all other adr's
sub L11_check_pn_availablility {
	
	my $adr = ""; 
	
	print "\n~~~~~~~ Finding Tryout devices - Level 11 search with same emmc,SXM,GNSS,FPGA, but can be different board-id , ADR & customer ~~~~~~~\n";
	$adr = $pndetails_hash{$findpn}{$h_adr};
	## To avoid the adr in device filtering basic adr is used. 
	if ($adr eq 'AARS_IVI_S2_AC_FM') {

		$adr = "-"; 
	}

	
	
	return OC_check_pn_availablility ($pndetails_hash{$findpn}{$h_emmc1},"-",$adr,
										$pndetails_hash{$findpn}{$h_sxm},$pndetails_hash{$findpn}{$h_teseo},$pndetails_hash{$findpn}{$h_fpga},$pndetails_hash{$findpn}{$h_cpld});
}
#####################################################################################################################################################################################################
## -> L12_check_pn_availablility - doesnot consider Board-id, customer, if ADR is FM then consider all other adr's, if CPLD/FPGA is not updatable then donot consider it. 
sub L12_check_pn_availablility {
	
	my $adr = ""; 
	my $GNSS = "";
	my $fpga = "";
	my $cpld = "";
	my $sxm = "";
	
	print "\n~~~~~~~ Finding Tryout devices - Level 12 search with same emmc, but with different board-id,customer,ADR,SXM,GNSS,FPGA,CPLD ~~~~~~~\n";
	
	$GNSS = $pndetails_hash{$findpn}{$h_teseo};
	if ( $GNSS eq 'Teseo_not_updatable') {
		$GNSS = "-";
	}
	elsif ( $GNSS eq 'UBlox_updatable') {
		$GNSS = "-";
	} 
	
	
	$fpga = $pndetails_hash{$findpn}{$h_fpga};
	$cpld = $pndetails_hash{$findpn}{$h_cpld};
	if ($fpga eq 'FPGA_and_CPLD_not_updatable') {
		$fpga = "-";
		$cpld = "-"
	}
	
	$sxm = $pndetails_hash{$findpn}{$h_sxm};
	if ($sxm eq 'SXM_not_updatable') {
		$sxm = "-";
	}
	
	$adr = $pndetails_hash{$findpn}{$h_adr};
	## To avoid the adr in device filtering basic adr is used. 
	if ($adr eq 'AARS_IVI_S2_AC_FM') {

		$adr = "-"; 
	}

	return OC_check_pn_availablility ($pndetails_hash{$findpn}{$h_emmc1},"-",$adr,$sxm,$GNSS,$fpga,$cpld);
}
#####################################################################################################################################################################################################
# Syntax to call --> OL_check_pn_availablility ( mydevice_emmc , mydeviceboardid , mydeviceadr , mydevicesxm , mydeviceteseo , mydevicefpga , mydevicecpld )
sub OL_check_pn_availablility {

	my $mydevice_emmc = shift||"";
	my $mydeviceboardid = shift||"";
	my $mydeviceadr = shift||"";
	my $mydevicesxm = shift||"";
	my $mydeviceteseo = shift||"";
	my $mydevicefpga = shift||"";
	my $mydevicecpld = shift||"";
	my @mydevicepns = @_;
	my $mydevicecustomer = $pndetails_hash{$findpn}{$h_customer};

	my @header_arr;
	my @CC_pns_arr;
	my $devicefound = 0;
	my $totaldevices = 0;
	my $_header_boardid_col;
	my $_header_adr_col ;
	my $_header_sxm_col;
	my $_header_teseo_col;
	my $_header_fpga_col;
	my $_header_cpld_col;
	my $_header_boschpn_col;
	my $_header_fcid_col; 
	my $_header_customer_col;
	
	# print "\n Filter On = $mydevice_emmc,$mydeviceboardid,$mydeviceadr,$mydevicesxm,$mydeviceteseo,$mydevicefpga,$mydevicecpld \n";

	my $total_devices = 0; 
	my $length_mydevicepns = @mydevicepns;
	
	if ($length_mydevicepns != 0) {
		$totaldevices = search_in_pool ($mydevice_emmc,$mydeviceboardid,$mydeviceadr,$mydevicesxm,$mydeviceteseo,$mydevicefpga,$mydevicecpld,$mydevicecustomer,@mydevicepns);
		goto Show_Device_Status;
	}
	
	
	my ($_header_row1,$_header_emmc_col) = Search_text_in_excel($E_worksheet_fcid,0,"(1st eMMC)",3,"-");
	
	## find the header of each columns in FCID table ##
	for (my $col = 1 ; $col <= $E_worksheet_fcid->UsedRange->Columns->{'Count'} ; $col++) {
		next unless defined $E_worksheet_fcid->Cells($_header_row1,$col)->{'Value'};
		my $cellheader = $E_worksheet_fcid->Cells($_header_row1,$col)->{'Value'};
		
		if ( $mydeviceboardid ne "" && index($cellheader,$h_boardid) != -1) {
			$_header_boardid_col = $col; 
			#print "_header_boardid_col = $h_boardid on $_header_boardid_col";
		}
		if ( $mydeviceadr ne "" && index($cellheader,$h_adr) != -1) {
			$_header_adr_col = $col; 
			#print "h_adr = $h_adr on $_header_adr_col";
		}
		if ( $mydevicesxm ne "" && index($cellheader,$h_sxm) != -1) {
			$_header_sxm_col = $col; 
			#print "h_sxm = $h_sxm on $_header_sxm_col";
		}
		if ( $mydeviceteseo ne "" &&  index($cellheader,$h_teseo) != -1) {
			$_header_teseo_col = $col; 
			#print "_header_teseo_col = $h_teseo on $_header_teseo_col";
		}
		if ( $mydevicefpga ne "" && index($cellheader,$h_fpga) != -1) {
			$_header_fpga_col = $col; 
			#print "_header_fpga_col = $h_teseo on $_header_fpga_col";
		}
		if ( $mydevicecpld ne "" && index($cellheader,$h_cpld) != -1) {
			$_header_cpld_col = $col; 
			#print "_header_cpld_col = $h_teseo on $_header_cpld_col";
		}
		if ( index($cellheader,$h_bosch_pn) != -1) {
			$_header_boschpn_col = $col; 
			#print "_header_boschpn_col = $h_teseo on $_header_boschpn_col";
		}
		if ( index($cellheader,$h_fcid) != -1) {
			$_header_fcid_col = $col; 
			#print "_header_boschpn_col = $h_teseo on $_header_boschpn_col";
		}
		if ( index($cellheader,$h_customer) != -1) {
			$_header_customer_col = $col; 
			#print "_header_boschpn_col = $h_teseo on $_header_boschpn_col";
		}
		
		#$header_arr[$i] = $E_worksheet_fcid->Cells($_header_row1,$i)->{'Value'};
	}
	
		#$emmc =~ s/\n|\.|-//g;
		print "PN - $mydevice_emmc" if $debug;
		my ($row,$col) = Search_text_in_excel($E_worksheet_fcid,1,$mydevice_emmc,"-","-");
		
		
		for (my $pndetails_rows = $row; $pndetails_rows <= $E_worksheet_fcid->UsedRange->Rows->{'Count'} ;$pndetails_rows++ ) { 
			#print "Row no - $pndetails_rows\n";
			my $curr_row_emmc = "";
			my $curr_row_boardid = "";
			my $curr_row_adr = "";
			my $curr_row_sxm =  "";
			my $curr_row_teseo = "";
			my $curr_row_fpga = "";
			my $curr_row_cpld = "";
			my $curr_row_boschpns = "";
			my $curr_row_fcid = "";
			my $curr_row_customer = "";
			
			if ( $_header_emmc_col ne "" ) { 
				#print "Cell value _header_emmc_col = $_header_emmc_col \n";
				$curr_row_emmc = $E_worksheet_fcid->Cells($pndetails_rows,$_header_emmc_col)->{'Value'}; 
				chomp($curr_row_emmc);
			}
			if ( $mydeviceboardid ne "" ) { 
				#print "Cell value mydeviceboardid = $mydeviceboardid \n";
				$curr_row_boardid = $E_worksheet_fcid->Cells($pndetails_rows,$_header_boardid_col)->{'Value'};
				chomp($curr_row_boardid);
			}
			if ( $mydeviceadr ne "" ) { 
				#print "Cell value mydeviceadr = $mydeviceadr \n";
				$curr_row_adr = $E_worksheet_fcid->Cells($pndetails_rows,$_header_adr_col)->{'Value'};
				chomp($curr_row_adr);
			}
			if ( $mydevicesxm ne "" ) { 
				#print "Cell value mydevicesxm = $mydevicesxm \n";
				$curr_row_sxm = $E_worksheet_fcid->Cells($pndetails_rows,$_header_sxm_col)->{'Value'};
				chomp($curr_row_sxm);
			}
			if ( $mydeviceteseo ne "" ) { 
				#print "Cell value mydeviceteseo = $mydeviceteseo \n";
				$curr_row_teseo = $E_worksheet_fcid->Cells($pndetails_rows,$_header_teseo_col)->{'Value'};
				chomp($curr_row_teseo);
			}
			if ( $mydevicefpga ne "" ) { 
				#print "Cell value mydevicefpga = $mydevicefpga \n";
				$curr_row_fpga = $E_worksheet_fcid->Cells($pndetails_rows,$_header_fpga_col)->{'Value'};
				chomp($curr_row_fpga);
			}
			if ( $mydevicecpld ne "" ) { 
				#print "Cell value mydevicefpga = $mydevicefpga \n";
				$curr_row_cpld = $E_worksheet_fcid->Cells($pndetails_rows,$_header_cpld_col)->{'Value'};
				chomp($curr_row_cpld);
			}
			if ( $mydevicecpld ne "" ) { 
				#print "Cell value mydevicefpga = $mydevicefpga \n";
				$curr_row_fcid = $E_worksheet_fcid->Cells($pndetails_rows,$_header_fcid_col)->{'Value'};
				chomp($curr_row_fcid);
			}
			$curr_row_customer = $E_worksheet_fcid->Cells($pndetails_rows,$_header_customer_col)->{'Value'};
			$curr_row_boschpns = $E_worksheet_fcid->Cells($pndetails_rows,$_header_boschpn_col)->{'Value'};
			
			#print "\n Current cell device details= $curr_row_emmc,$curr_row_boardid,$curr_row_adr,$curr_row_sxm,$curr_row_teseo,$curr_row_fpga,$curr_row_cpld,$curr_row_boschpns \n";
			# print "\n Current Filter On = $mydevice_emmc,$mydeviceboardid,$mydeviceadr,$mydevicesxm,$mydeviceteseo,$mydevicefpga,$mydevicecpld \n";
			next unless defined $curr_row_boschpns; ## skip to next line if PNs cell is empty
			if ((($mydevice_emmc ne "" && $mydevice_emmc ne '-')? $mydevice_emmc eq $curr_row_emmc : ($mydevice_emmc eq '-' ?1:0)) && 
					(($mydeviceboardid ne "" && $mydeviceboardid ne '-') ? $mydeviceboardid eq $curr_row_boardid :($mydeviceboardid eq '-' ?1:0)) &&
						(($mydeviceadr ne "" && $mydeviceadr ne '-') ? $mydeviceadr eq $curr_row_adr :($mydeviceadr eq '-' ?1:0)) && 
							(($mydevicesxm ne "" && $mydevicesxm ne '-')  ? $mydevicesxm eq $curr_row_sxm:($mydevicesxm eq '-' ? 1 : 0)) && 
								(($mydeviceteseo ne "" && $mydeviceteseo ne '-') ? $mydeviceteseo eq $curr_row_teseo: ($mydeviceteseo eq '-' ? 1 : 0)) &&
									 (($mydevicefpga ne "" && $mydevicefpga ne '-') ? $mydevicefpga eq $curr_row_fpga: ($mydevicefpga eq '-' ? 1 : 0)) && 
										(($mydevicecpld ne "" && $mydevicecpld ne '-') ? $mydevicecpld eq $curr_row_cpld:($mydevicecpld eq '-' ? 1 : 0)) &&
											($mydevicecustomer eq $curr_row_customer ))  { 
				
				$curr_row_boschpns =~ s/\n/ /g;
				@CC_pns_arr = split(',',$curr_row_boschpns);
				$devicefound = search_in_pool ($curr_row_emmc,$curr_row_boardid,$curr_row_adr,$curr_row_sxm,$curr_row_teseo,$curr_row_fpga,$curr_row_cpld,$curr_row_customer,@CC_pns_arr);
				$totaldevices = $totaldevices + $devicefound;
			}
		
		
			
		}
		
	Show_Device_Status:
	if ($totaldevices == 0){
		print "\n\n!!!! No Devices found !!!!\n";
		return $totaldevices;
	}	
	else {
		print "\n\n*****  Total no of Tryout devices found = $totaldevices *****\n";
		return $totaldevices;
	}
	
	
}
#####################################################################################################################################################################################################
# Syntax to call --> OC_check_pn_availablility ( mydevice_emmc , mydeviceboardid , mydeviceadr , mydevicesxm , mydeviceteseo , mydevicefpga , mydevicecpld ) here customer is not taken for comparison
sub OC_check_pn_availablility {

	my $mydevice_emmc = shift||"";
	my $mydeviceboardid = shift||"";
	my $mydeviceadr = shift||"";
	my $mydevicesxm = shift||"";
	my $mydeviceteseo = shift||"";
	my $mydevicefpga = shift||"";
	my $mydevicecpld = shift||"";
	my @mydevicepns = @_;
	#my $mydevicecustomer = $pndetails_hash{$findpn}{$h_customer};

	my @header_arr;
	my @CC_pns_arr;
	my $devicefound = 0;
	my $totaldevices = 0;
	my $_header_boardid_col;
	my $_header_adr_col ;
	my $_header_sxm_col;
	my $_header_teseo_col;
	my $_header_fpga_col;
	my $_header_cpld_col;
	my $_header_boschpn_col;
	my $_header_fcid_col; 
	my $_header_customer_col;
	
	# print "\n Filter On = $mydevice_emmc,$mydeviceboardid,$mydeviceadr,$mydevicesxm,$mydeviceteseo,$mydevicefpga,$mydevicecpld \n";

	my $total_devices = 0; 
	my $length_mydevicepns = @mydevicepns;
	
	if ($length_mydevicepns != 0) {
		$totaldevices = search_in_pool ($mydevice_emmc,$mydeviceboardid,$mydeviceadr,$mydevicesxm,$mydeviceteseo,$mydevicefpga,$mydevicecpld,@mydevicepns);
		goto Show_Device_Status;
	}
	
	
	my ($_header_row1,$_header_emmc_col) = Search_text_in_excel($E_worksheet_fcid,0,"(1st eMMC)",3,"-");
	
	## find the header of each columns in FCID table ##
	for (my $col = 1 ; $col <= $E_worksheet_fcid->UsedRange->Columns->{'Count'} ; $col++) {
		next unless defined $E_worksheet_fcid->Cells($_header_row1,$col)->{'Value'};
		my $cellheader = $E_worksheet_fcid->Cells($_header_row1,$col)->{'Value'};
		
		if ( $mydeviceboardid ne "" && index($cellheader,$h_boardid) != -1) {
			$_header_boardid_col = $col; 
			#print "_header_boardid_col = $h_boardid on $_header_boardid_col";
		}
		if ( $mydeviceadr ne "" && index($cellheader,$h_adr) != -1) {
			$_header_adr_col = $col; 
			#print "h_adr = $h_adr on $_header_adr_col";
		}
		if ( $mydevicesxm ne "" && index($cellheader,$h_sxm) != -1) {
			$_header_sxm_col = $col; 
			#print "h_sxm = $h_sxm on $_header_sxm_col";
		}
		if ( $mydeviceteseo ne "" &&  index($cellheader,$h_teseo) != -1) {
			$_header_teseo_col = $col; 
			#print "_header_teseo_col = $h_teseo on $_header_teseo_col";
		}
		if ( $mydevicefpga ne "" && index($cellheader,$h_fpga) != -1) {
			$_header_fpga_col = $col; 
			#print "_header_fpga_col = $h_teseo on $_header_fpga_col";
		}
		if ( $mydevicecpld ne "" && index($cellheader,$h_cpld) != -1) {
			$_header_cpld_col = $col; 
			#print "_header_cpld_col = $h_teseo on $_header_cpld_col";
		}
		if ( index($cellheader,$h_bosch_pn) != -1) {
			$_header_boschpn_col = $col; 
			#print "_header_boschpn_col = $h_teseo on $_header_boschpn_col";
		}
		if ( index($cellheader,$h_fcid) != -1) {
			$_header_fcid_col = $col; 
			#print "_header_boschpn_col = $h_teseo on $_header_boschpn_col";
		}
		if ( index($cellheader,$h_customer) != -1) {
			$_header_customer_col = $col; 
			#print "_header_boschpn_col = $h_teseo on $_header_boschpn_col";
		}
		
		#$header_arr[$i] = $E_worksheet_fcid->Cells($_header_row1,$i)->{'Value'};
	}
	
		#$emmc =~ s/\n|\.|-//g;
		print "PN - $mydevice_emmc" if $debug;
		my ($row,$col) = Search_text_in_excel($E_worksheet_fcid,1,$mydevice_emmc,"-","-");
		
		
		for (my $pndetails_rows = $row; $pndetails_rows <= $E_worksheet_fcid->UsedRange->Rows->{'Count'} ;$pndetails_rows++ ) { 
			#print "Row no - $pndetails_rows\n";
			my $curr_row_emmc = "";
			my $curr_row_boardid = "";
			my $curr_row_adr = "";
			my $curr_row_sxm =  "";
			my $curr_row_teseo = "";
			my $curr_row_fpga = "";
			my $curr_row_cpld = "";
			my $curr_row_boschpns = "";
			my $curr_row_fcid = "";
			my $curr_row_customer = "";
			
			if ( $_header_emmc_col ne "" ) { 
				#print "Cell value _header_emmc_col = $_header_emmc_col \n";
				$curr_row_emmc = $E_worksheet_fcid->Cells($pndetails_rows,$_header_emmc_col)->{'Value'}; 
				chomp($curr_row_emmc);
			}
			if ( $mydeviceboardid ne "" ) { 
				#print "Cell value mydeviceboardid = $mydeviceboardid \n";
				$curr_row_boardid = $E_worksheet_fcid->Cells($pndetails_rows,$_header_boardid_col)->{'Value'};
				chomp($curr_row_boardid);
			}
			if ( $mydeviceadr ne "" ) { 
				#print "Cell value mydeviceadr = $mydeviceadr \n";
				$curr_row_adr = $E_worksheet_fcid->Cells($pndetails_rows,$_header_adr_col)->{'Value'};
				chomp($curr_row_adr);
			}
			if ( $mydevicesxm ne "" ) { 
				#print "Cell value mydevicesxm = $mydevicesxm \n";
				$curr_row_sxm = $E_worksheet_fcid->Cells($pndetails_rows,$_header_sxm_col)->{'Value'};
				chomp($curr_row_sxm);
			}
			if ( $mydeviceteseo ne "" ) { 
				#print "Cell value mydeviceteseo = $mydeviceteseo \n";
				$curr_row_teseo = $E_worksheet_fcid->Cells($pndetails_rows,$_header_teseo_col)->{'Value'};
				chomp($curr_row_teseo);
			}
			if ( $mydevicefpga ne "" ) { 
				#print "Cell value mydevicefpga = $mydevicefpga \n";
				$curr_row_fpga = $E_worksheet_fcid->Cells($pndetails_rows,$_header_fpga_col)->{'Value'};
				chomp($curr_row_fpga);
			}
			if ( $mydevicecpld ne "" ) { 
				#print "Cell value mydevicefpga = $mydevicefpga \n";
				$curr_row_cpld = $E_worksheet_fcid->Cells($pndetails_rows,$_header_cpld_col)->{'Value'};
				chomp($curr_row_cpld);
			}
			if ( $mydevicecpld ne "" ) { 
				#print "Cell value mydevicefpga = $mydevicefpga \n";
				$curr_row_fcid = $E_worksheet_fcid->Cells($pndetails_rows,$_header_fcid_col)->{'Value'};
				chomp($curr_row_fcid);
			}
			$curr_row_customer = $E_worksheet_fcid->Cells($pndetails_rows,$_header_customer_col)->{'Value'};
			$curr_row_boschpns = $E_worksheet_fcid->Cells($pndetails_rows,$_header_boschpn_col)->{'Value'};
			
			#print "\n Current cell device details= $curr_row_emmc,$curr_row_boardid,$curr_row_adr,$curr_row_sxm,$curr_row_teseo,$curr_row_fpga,$curr_row_cpld,$curr_row_boschpns \n";
			# print "\n Current Filter On = $mydevice_emmc,$mydeviceboardid,$mydeviceadr,$mydevicesxm,$mydeviceteseo,$mydevicefpga,$mydevicecpld \n";
			next unless defined $curr_row_boschpns; ## skip to next line if PNs cell is empty
			if ((($mydevice_emmc ne "" && $mydevice_emmc ne '-')? $mydevice_emmc eq $curr_row_emmc : ($mydevice_emmc eq '-' ?1:0)) && 
					(($mydeviceboardid ne "" && $mydeviceboardid ne '-') ? $mydeviceboardid eq $curr_row_boardid :($mydeviceboardid eq '-' ?1:0)) &&
						(($mydeviceadr ne "" && $mydeviceadr ne '-') ? $mydeviceadr eq $curr_row_adr :($mydeviceadr eq '-' ?1:0)) && 
							(($mydevicesxm ne "" && $mydevicesxm ne '-')  ? $mydevicesxm eq $curr_row_sxm:($mydevicesxm eq '-' ? 1 : 0)) && 
								(($mydeviceteseo ne "" && $mydeviceteseo ne '-') ? $mydeviceteseo eq $curr_row_teseo: ($mydeviceteseo eq '-' ? 1 : 0)) &&
									 (($mydevicefpga ne "" && $mydevicefpga ne '-') ? $mydevicefpga eq $curr_row_fpga: ($mydevicefpga eq '-' ? 1 : 0)) && 
										(($mydevicecpld ne "" && $mydevicecpld ne '-') ? $mydevicecpld eq $curr_row_cpld:($mydevicecpld eq '-' ? 1 : 0)))  { 
				
				$curr_row_boschpns =~ s/\n/ /g;
				@CC_pns_arr = split(',',$curr_row_boschpns);
				$devicefound = search_in_pool ($curr_row_emmc,$curr_row_boardid,$curr_row_adr,$curr_row_sxm,$curr_row_teseo,$curr_row_fpga,$curr_row_cpld,$curr_row_customer,@CC_pns_arr);
				$totaldevices = $totaldevices + $devicefound;
			}
		
		
			
		}
		
	Show_Device_Status:
	if ($totaldevices == 0){
		print "\n\n!!!! No Devices found !!!!\n";
		return $totaldevices;
	}	
	else {
		print "\n\n*****  Total no of Tryout devices found = $totaldevices *****\n";
		return $totaldevices;
	}
	
	
}
#####################################################################################################################################################################################################
## $curr_row_emmc,$curr_row_boardid,$curr_row_adr,$curr_row_sxm,$curr_row_teseo,$curr_row_fpga,$curr_row_cpld,$curr_row_customer,$curr_row_boschpns
sub search_in_pool {	
my $curr_row_emmc = shift;
my $curr_row_boardid = shift;
my $curr_row_adr = shift;
my $curr_row_sxm = shift;
my $curr_row_teseo = shift;
my $curr_row_fpga = shift;
my $curr_row_cpld = shift;
my $curr_row_customer= shift;
#my $curr_row_boschpns = @_;
my @CC_pns_arr = @_;
my $HW_Key_header_col;
my $total_devices = 0;
my $headerkeyword = "Part No";

	#print "\nsheet name = $sheet_name\n";
	#$E_worksheet_hwlist = E_Open($xl_hwlist,$sheet_name);
	#print "\nlist = @CC_pns_arr\n";
	#my $totalsheet= $E_workbook_hwlist->Worksheets->Count;
	
	#foreach my $sheet (1...$totalsheet) {
		$E_worksheet_hwlist = $E_workbook_hwlist->WorkSheets($sheet_name);
		$E_worksheet_hwlist ->Activate(); 
		#print "\n\n\n\n $sheet\n\n\n";
		my $hw_h_row;
		my $hw_h_col;
		######## Find the header of HWlist JIRA Dump #######
		($hw_h_row,$hw_h_col) = Search_text_in_excel($E_worksheet_hwlist,1,$headerkeyword,"-","-"); 
		#print "($hw_h_row,$hw_h_col)";	
		if ($hw_h_row == 0 && $hw_h_col == 0){ next; } ## Switch to next sheet, if the current sheet doesnot have the key word
		
		for (my $i = 1 ; $i <= $E_worksheet_hwlist->UsedRange->Columns->{'Count'} ; $i++) {
			next unless defined $E_worksheet_hwlist->Cells($hw_h_row,$i)->{'Value'};
			if ($E_worksheet_hwlist->Cells($hw_h_row,$i)->{'Value'} eq $headerkeyword) {
				$HW_Key_header_col = $i;
				#print "HW_Key_header_col - $HW_Key_header_col \n";
			}
		}
		#@CC_pns_arr = split(',',$curr_row_boschpns);
		#print "\n@CC_pns_arr\n";
		foreach my $pn (@CC_pns_arr) {
			$pn =~ s/\n|\.|-|\s+//g;
			chomp($pn);
			#print "PN - \"$pn\"";
			my ($row,$col) = Search_text_in_excel($E_worksheet_hwlist,1,$pn,"-","-");
			
			
			if ($row != 0 && $col != 0) {
			#print "device number = $col $row  \n";
			my  $bef_col = $col-1 ;
			#$new_spl_wk_sheet->Cells($ECR_row,$ECR_col)->{'Value'}= $overall_info{ecr};
			my $dv_id = $E_worksheet_hwlist->Cells($row,$bef_col)->{'Value'};
			#print "device number = $dv_id  \n";
			
				print "\n  Hardware Partnumber \"$pn - $dv_id\" is found in device pool (".$E_worksheet_hwlist->Name.")"; 
				$total_devices ++; 
				for (my $pndetails_col = $HW_Key_header_col; $pndetails_col <= $HW_Key_header_col;$pndetails_col++ ) {
					next unless defined $E_worksheet_hwlist->Cells($row,$pndetails_col)->{'Value'};
					print "\n   |__". $E_worksheet_hwlist->Cells($row,$pndetails_col)->{'Value'};
					print " --> ". $curr_row_emmc ." / ". $curr_row_boardid ." / ". $curr_row_adr ." / ". $curr_row_sxm ." / ". $curr_row_teseo ." / ". $curr_row_fpga ." / ". $curr_row_cpld ." / ". $curr_row_customer."\n";
					print "\n   |^_". $adr_info ."/". $E_worksheet_hwlist->Cells($row,$pndetails_col)->{'Value'} ."-". ($dv_id) ."/". $curr_row_boardid ."/". $curr_row_adr ."_^|" ;
					#print " --> ". $curr_row_emmc ." / ". $curr_row_boardid ." / ". $curr_row_adr ." / ". $curr_row_sxm ." / ". $curr_row_teseo ." / ". $curr_row_fpga ." / ". $curr_row_cpld ." / ". $curr_row_customer."\n";
				}
				
			}
		}
	#}	
	if ($total_devices == 0){
		#print "\n\n!!!! No Devices found !!!!\n";
		return $total_devices;
	}	
	else {
		#print "\n\n*****  Total no of Tryout devices found = $total_devices *****\n";
		return $total_devices;
	}
	
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
		'hwlist=s' => \$xl_hwlist,
		'fcid=s'   => \$xl_fcidtable,
		'p=s'		 => \$findpn,
		'v'        => \$debug,
	) or die("$help_text");
	  
		if ($h) {
		print $help_text;
		exit(0);
	}
	  
	if ($xl_hwlist) {
		$xl_hwlist = check_file($xl_hwlist);
		chomp($xl_hwlist);
	}
	else {
		print ("HW Pool Excel dump is missing\n");
	}
	if ($xl_fcidtable) {
		$xl_fcidtable = check_file($xl_fcidtable);
		chomp($xl_fcidtable);
	}
	else {
		print ("JIRA Task dump Excel input file is missing\n");
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
#####################################################################################################################################################################################################
# Open Excelsheet
#
sub E_Open {
  my $E_file  = shift;
  my $sheet   = shift;
  print "sheet name first = $sheet \n";
	#exit_script(1);
  if (! (-f "$E_file") ) {
    $error_string  .= "$E_file cannot be opened or does not exists!\n";
    return 1;
  }
  print "Open $sheet in $E_file...\n";
  $E_workbook   = $E_excel->Workbooks->Open("$E_file");
  $E_worksheet  = $E_workbook->WorkSheets("$sheet");
  $E_worksheet  -> Activate();
  return 0;
}
#################################################################################################################
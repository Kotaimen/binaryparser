import io
import sys, os, os.path
sys.path.insert(0, '../src')


from binaryparser import *

MapLonLat = Structure('LonLat', 
    Int32('Lon'),
    Int32('Lat'),
    )
    
MapSeiki = Structure('Seiki',
    Int16('X'),
    Int16('Y')
    )

AbsLinkID = Structure('AbsLinkId',
    Hex(WORD('SLinkId1')),
    Hex(WORD('SLinkId2')),
    Hex(WORD('ELinkId')),
    #Calculate('LinkId', lambda c: '{:x}:{:x}'.format(((c.SLinkId1 << 16) & c.SLinkId2), c.ELinkId)),
    
    )

PDM_ResultLinkInfo = Structure('ResultLinkInfo',
    AbsLinkID,
    WORD('Layer'),
    WORD('GuideInfo'),
    WORD('LinkInfo'),
    WORD('LinkKind'),
    WORD('RoadID'),
    Rename('Coord', MapSeiki),
    )

PDM_ResultPathInfoHeader = Structure('ResultPathInfoHeader',
    Int16('LinkNum'),
    Int16('ParcelChangeNum'),
    Int16('StartLinkNum'),
    Int16('HighwayIdNum'),
    WORD('LinkInfoOffset'),
    WORD('ParcelIdOffset'),
    WORD('HighwayIdOffset'),
    Array('EndLonLat', MapLonLat, 2),
)

PDM_ResultPathInfo = Structure('ResultPathInfo',
    PDM_ResultPathInfoHeader,
    Array('LinkString', PDM_ResultLinkInfo, lambda c: c.ResultPathInfoHeader.LinkNum)
    
    )

PDM_ResultAllInfo = Structure('ResultAllInfo',
    PDM_ResultPathInfo,
    
    )

PDM_ResultSaveInfo = Structure('ResultSaveInfo',
    WORD('RouteInfo'),
    Structure('NextTrigger',
        WORD('LinkId1'),
        WORD('LinkId2'),
        Calculate('LinkId', lambda c: hex(c.LinkId1 << 16 & c.LinkId2)),
        WORD('LinkNo'),
        ),
    Structure('IntellgentRerouteInfo',
        BYTE('CostType'),
        BYTE('RouteCount'),
        BYTE('NoCostRouteCount'),
        BYTE('DetourRouteCount'),
        BYTE('CurrentRouteCount'),
        BYTE('OtherRouteControlFlag'),
        WORD('PreviousRoadKind'),
    )
)

PDM_ResultSetAllInfo = Structure('ResultSetAllInfo',
    DWORD('SerialNo'),
    PDM_ResultSaveInfo,
    PDM_ResultAllInfo,
    )

PDM_ResultFileFormat = Structure('ResultFormat',
    PDM_ResultSetAllInfo,
    )
    
def main():
    with open('0002.dat', 'rb') as fp:
        r = PDM_ResultFileFormat.parse(fp)
        view_context(r)
        pretty_print(r)
        
if __name__ == '__main__':
    main()
    
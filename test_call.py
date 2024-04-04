from pprint import pprint
import pyrfc

class sap_general():

    def check_sap_table_record_length(self, table, list_fields=''):
        """
        :param table: Table Name in the SAP dictionary
        :param list_fields: optional list of fields
        :rtype : row length as integer
        """
        result = self.call('DDIF_FIELDINFO_GET', TABNAME=table)
        tabdef = result['DFIES_TAB']
        recordlength=0
        if list_fields == "":
            for field in tabdef:
                recordlength = recordlength + int(field['LENG'])
        else:
            for field in tabdef:
                field_name = str(field['FIELDNAME']).strip()
                if field_name in list_fields:
                    recordlength = recordlength + int(field['LENG'])
        return(int(recordlength))

    def download_sap_table_to_memory(self, tabname, **kwargs):
        import sys
        '''Downloads a given SAP table and returns it as list of dictionaries

        :param tabname: Table name
        :param kwargs: dictionary that contains additional parameters:

        whereclause: where clause to restrict the number of records read via RFC (ABAP Syntax)
        tabfields: list of columns that should be downloaded
        customfields: add custom fields
        fetchsize: package size that defines the number of records to download per RFC call. Default value is 1000
        droptable: check whether a table should be dropped if it already exists. Default is yes.

        '''

        parameters = dict()
        parameters['QUERY_TABLE']=tabname
        if 'whereclause' in kwargs.keys():
            parameters['OPTIONS']=[kwargs['whereclause']]

        if 'tabfields' in kwargs.keys():
            tabfields=kwargs['tabfields']
    #        parameters['FIELDS']=tabfields
            for field in kwargs['tabfields']:
                parameters['FIELDS'].append([field])
        else:
            tabfields=''

        if 'fetchsize' in kwargs.keys():
            parameters['ROWCOUNT'] = kwargs['fetchsize']
            fetchsize = kwargs['fetchsize']
        else:
            parameters['ROWCOUNT'] = 1000
            fetchsize = 1000

        tabsize = self.check_sap_table_record_length(tabname, tabfields)
        print ("-checking column size limit")
        if tabsize >= 512:
            print("-column length > RFC_READ_TABLE limit")
            sys.exit(1)
        else:
            recordcounter = 1
            iteration = 0
            tempresult = self.call('RFC_READ_TABLE', NO_DATA='X', **parameters)
            tabdef = tempresult['FIELDS']

            result=[]
            while recordcounter > 0:
                tempresult = self.call('RFC_READ_TABLE', ROWSKIPS=iteration*fetchsize,  **parameters)
                iteration=iteration+1
                data = tempresult['DATA']
                if len(data) > 0:
                    for row in data:
                        tempresultrow=dict()
                        for columndef in tabdef:
                            columnname=columndef['FIELDNAME'].strip()
                            offset=int(columndef['OFFSET'])
                            length=int(columndef['LENGTH'])
                            value=row['WA'][offset:offset+length]
                            value=value.strip()
                            if value == '':
                                value=' '
                            tempresultrow[columnname]=value
                        result.append(tempresultrow)
                else:
                    recordcounter=0
        return(result)



class sap_instance(pyrfc.Connection, sap_general):
    def __init__(self, *args, **kwargs ):
        pyrfc.Connection.__init__(self, *args, **kwargs )
        self.condetails=self.get_connection_attributes()
        self.sap_general=sap_general()


if __name__ == '__main__':
    params = {'user'  : 'user',
              'passwd': 'password',
              'ashost': 'hostname',
              'sysnr' : '00',
              'client': 'x00'}
    conn2=sap_instance(**params)
    result=conn2.download_sap_table_to_memory('T000')
    pprint(result)



